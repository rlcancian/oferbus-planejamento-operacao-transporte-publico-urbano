from __future__ import annotations

import uuid
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from oferbus_core import (
    CostPlanningInput,
    ObservedTripInput,
    PlanningSpecification,
    SemanticLayer,
    VehiclePlanningInput,
    fingerprint,
)
from oferbus_planning import (
    CreateObservedDatasetCommand,
    CreateObservedDatasetRevisionCommand,
    CreateScenarioRevisionCommand,
    DirectionObservationBatch,
    DirectionPlanningSnapshotCommand,
    PlanningInputError,
    PlanningInputIntegrityError,
    PlanningInputNotFound,
    create_observed_dataset,
    create_observed_dataset_revision,
    create_scenario_revision,
    load_planning_input,
)

from .identity import Permission, Principal, require_permission


class ObservedTripRequest(BaseModel):
    departure_service_minute: int = Field(ge=0)
    passengers: int = Field(ge=0)
    critical_passengers: int = Field(default=0, ge=0)
    travel_time_min: int = Field(default=0, ge=0)


class DatasetDirectionRequest(BaseModel):
    direction_id: uuid.UUID
    observations: list[ObservedTripRequest] = Field(min_length=1)


class ObservedDatasetCreateRequest(BaseModel):
    line_id: uuid.UUID
    name: str = Field(min_length=1, max_length=240)
    description: str | None = None
    source_label: str | None = Field(default=None, max_length=240)
    source_metadata: dict[str, Any] | None = None
    directions: list[DatasetDirectionRequest] = Field(min_length=1)


class ObservedDatasetRevisionCreateRequest(BaseModel):
    parent_revision_id: uuid.UUID | None = None
    source_label: str | None = Field(default=None, max_length=240)
    source_metadata: dict[str, Any] | None = None
    directions: list[DatasetDirectionRequest] = Field(min_length=1)


class ObservedDatasetCreateResponse(BaseModel):
    dataset_id: uuid.UUID
    dataset_revision_id: uuid.UUID
    revision_no: int
    content_fingerprint: str


class DirectionPlanningRequest(BaseModel):
    direction_id: uuid.UUID
    dataset_revision_id: uuid.UUID
    service_start_minute: int = Field(ge=0)
    service_end_minute: int = Field(ge=0)
    demand_passengers_per_minute: list[float] = Field(min_length=3)
    renewal_index_curve: list[float] = Field(min_length=3)
    travel_time_min_curve: list[float] = Field(min_length=3)
    demand_maximum_passengers_per_minute: float = Field(ge=0)
    storage_at_departure_terminal: bool


class VehiclePlanningRequest(BaseModel):
    seats: int = Field(ge=0)
    free_area_m2: float = Field(gt=0)
    capacity_level: int = Field(default=1, ge=0)


class CostPlanningRequest(BaseModel):
    mode: Literal["per_km", "fixed_variable"] = "per_km"
    cost_per_km: float = Field(default=0, ge=0)
    fixed_cost_per_vehicle: float = Field(default=0, ge=0)
    variable_cost_per_km: float = Field(default=0, ge=0)


class PlanningSpecificationRequest(BaseModel):
    max_headway_min: int = Field(gt=0)
    project_capacity_passengers: float = Field(gt=0)
    valley_capacity_passengers: float = Field(gt=0)
    boarding_seconds_per_passenger: float = Field(ge=0)
    alighting_seconds_per_passenger: float = Field(ge=0)
    radial: bool
    create_express_returns: bool = False
    mean_renewal_index: float = Field(default=1, gt=0)
    typical_day_participation: float = Field(default=1, ge=0)
    equivalent_passenger_index: float = Field(default=1, gt=0)


class ScenarioRevisionCreateRequest(BaseModel):
    scenario_id: uuid.UUID
    parent_revision_id: uuid.UUID | None = None
    reason: str | None = None
    semantic_layer: Literal["legacy-exact", "normalized", "modern"]
    vehicle: VehiclePlanningRequest
    cost: CostPlanningRequest
    specification: PlanningSpecificationRequest
    directions: list[DirectionPlanningRequest] = Field(min_length=1)


class PlanningInputResponse(BaseModel):
    scenario_revision_id: uuid.UUID
    revision_no: int | None = None
    input_fingerprint: str
    planning_input: dict[str, Any]


def _core_input_payload(value) -> dict[str, Any]:
    return {
        "semantic_layer": value.semantic_layer.value,
        "directions": [
            {
                "direction_key": direction.direction_key,
                "legacy_direction_number": direction.legacy_direction_number,
                "observations": [
                    {
                        "departure_service_minute": item.departure_service_minute,
                        "passengers": item.passengers,
                        "critical_passengers": item.critical_passengers,
                        "travel_time_min": item.travel_time_min,
                    }
                    for item in direction.observations
                ],
                "demand_passengers_per_minute": list(direction.demand_passengers_per_minute),
                "renewal_index_curve": list(direction.renewal_index_curve),
                "travel_time_min_curve": list(direction.travel_time_min_curve),
                "service_start_minute": direction.service_start_minute,
                "service_end_minute": direction.service_end_minute,
                "demand_maximum_passengers_per_minute": direction.demand_maximum_passengers_per_minute,
                "extension_km": direction.extension_km,
                "storage_at_departure_terminal": direction.storage_at_departure_terminal,
            }
            for direction in value.directions
        ],
        "vehicle": {
            "seats": value.vehicle.seats,
            "free_area_m2": value.vehicle.free_area_m2,
            "capacity_level": value.vehicle.capacity_level,
        },
        "cost": {
            "mode": value.cost.mode,
            "cost_per_km": value.cost.cost_per_km,
            "fixed_cost_per_vehicle": value.cost.fixed_cost_per_vehicle,
            "variable_cost_per_km": value.cost.variable_cost_per_km,
        },
        "specification": {
            "max_headway_min": value.specification.max_headway_min,
            "project_capacity_passengers": value.specification.project_capacity_passengers,
            "valley_capacity_passengers": value.specification.valley_capacity_passengers,
            "boarding_seconds_per_passenger": value.specification.boarding_seconds_per_passenger,
            "alighting_seconds_per_passenger": value.specification.alighting_seconds_per_passenger,
            "radial": value.specification.radial,
            "create_express_returns": value.specification.create_express_returns,
            "mean_renewal_index": value.specification.mean_renewal_index,
            "typical_day_participation": value.specification.typical_day_participation,
            "equivalent_passenger_index": value.specification.equivalent_passenger_index,
        },
    }


def _observation_batches(request_directions: list[DatasetDirectionRequest]) -> tuple[DirectionObservationBatch, ...]:
    return tuple(
        DirectionObservationBatch(
            direction_id=direction.direction_id,
            observations=tuple(
                ObservedTripInput(
                    departure_service_minute=item.departure_service_minute,
                    passengers=item.passengers,
                    critical_passengers=item.critical_passengers,
                    travel_time_min=item.travel_time_min,
                )
                for item in direction.observations
            ),
        )
        for direction in request_directions
    )


def _http_error(exc: PlanningInputError) -> HTTPException:
    if isinstance(exc, PlanningInputNotFound):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, PlanningInputIntegrityError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


router = APIRouter(prefix="/planning", tags=["planning"])


@router.post(
    "/datasets",
    response_model=ObservedDatasetCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_dataset(
    request: ObservedDatasetCreateRequest,
    principal: Principal = Depends(require_permission(Permission.PROJECT_WRITE)),
) -> ObservedDatasetCreateResponse:
    try:
        created = create_observed_dataset(
            CreateObservedDatasetCommand(
                organization_id=principal.organization_id,
                created_by=principal.user_id,
                line_id=request.line_id,
                name=request.name,
                description=request.description,
                source_label=request.source_label,
                source_metadata=request.source_metadata,
                directions=_observation_batches(request.directions),
            )
        )
    except PlanningInputError as exc:
        raise _http_error(exc) from exc
    return ObservedDatasetCreateResponse(**created.__dict__)


@router.post(
    "/datasets/{dataset_id}/revisions",
    response_model=ObservedDatasetCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_dataset_revision(
    dataset_id: uuid.UUID,
    request: ObservedDatasetRevisionCreateRequest,
    principal: Principal = Depends(require_permission(Permission.PROJECT_WRITE)),
) -> ObservedDatasetCreateResponse:
    try:
        created = create_observed_dataset_revision(
            CreateObservedDatasetRevisionCommand(
                organization_id=principal.organization_id,
                created_by=principal.user_id,
                dataset_id=dataset_id,
                parent_revision_id=request.parent_revision_id,
                source_label=request.source_label,
                source_metadata=request.source_metadata,
                directions=_observation_batches(request.directions),
            )
        )
    except PlanningInputError as exc:
        raise _http_error(exc) from exc
    return ObservedDatasetCreateResponse(**created.__dict__)


@router.post(
    "/scenario-revisions",
    response_model=PlanningInputResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_revision(
    request: ScenarioRevisionCreateRequest,
    principal: Principal = Depends(require_permission(Permission.SCENARIO_WRITE)),
) -> PlanningInputResponse:
    try:
        created = create_scenario_revision(
            CreateScenarioRevisionCommand(
                organization_id=principal.organization_id,
                created_by=principal.user_id,
                scenario_id=request.scenario_id,
                parent_revision_id=request.parent_revision_id,
                reason=request.reason,
                semantic_layer=SemanticLayer(request.semantic_layer),
                vehicle=VehiclePlanningInput(**request.vehicle.model_dump()),
                cost=CostPlanningInput(**request.cost.model_dump()),
                specification=PlanningSpecification(**request.specification.model_dump()),
                directions=tuple(
                    DirectionPlanningSnapshotCommand(
                        direction_id=item.direction_id,
                        dataset_revision_id=item.dataset_revision_id,
                        service_start_minute=item.service_start_minute,
                        service_end_minute=item.service_end_minute,
                        demand_passengers_per_minute=tuple(item.demand_passengers_per_minute),
                        renewal_index_curve=tuple(item.renewal_index_curve),
                        travel_time_min_curve=tuple(item.travel_time_min_curve),
                        demand_maximum_passengers_per_minute=item.demand_maximum_passengers_per_minute,
                        storage_at_departure_terminal=item.storage_at_departure_terminal,
                    )
                    for item in request.directions
                ),
            )
        )
    except PlanningInputError as exc:
        raise _http_error(exc) from exc

    return PlanningInputResponse(
        scenario_revision_id=created.scenario_revision_id,
        revision_no=created.revision_no,
        input_fingerprint=created.input_fingerprint,
        planning_input=_core_input_payload(created.planning_input),
    )


@router.get(
    "/scenario-revisions/{scenario_revision_id}/input",
    response_model=PlanningInputResponse,
)
def get_revision_input(
    scenario_revision_id: uuid.UUID,
    principal: Principal = Depends(require_permission(Permission.SCENARIO_READ)),
) -> PlanningInputResponse:
    try:
        planning_input = load_planning_input(principal.organization_id, scenario_revision_id)
    except PlanningInputError as exc:
        raise _http_error(exc) from exc

    return PlanningInputResponse(
        scenario_revision_id=scenario_revision_id,
        revision_no=None,
        input_fingerprint=fingerprint(planning_input),
        planning_input=_core_input_payload(planning_input),
    )
