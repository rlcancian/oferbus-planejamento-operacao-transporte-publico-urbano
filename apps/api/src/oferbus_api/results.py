from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from oferbus_db import (
    LineDirection,
    PlanRevision,
    PlanningProject,
    Scenario,
    ScenarioDirectionPlanningInput,
    ScenarioRevision,
    TransitLine,
)
from oferbus_planning import (
    PersistedPlanningResult,
    PlanningResultIntegrityError,
    PlanningResultNotFound,
    load_planning_result,
)

from .identity import Permission, Principal, database_session, require_permission


class PlannedTripResponse(BaseModel):
    sequence_no: int
    direction_key: str
    legacy_direction_number: int
    departure_service_minute: int
    arrival_service_minute: int
    virtual_departure_service_minute: int
    virtual_arrival_service_minute: int
    trip_type: int
    is_express: bool
    vehicle_block: int
    service_level: int | None


class VehicleBlockResponse(BaseModel):
    block_no: int
    trip_sequence_nos: list[int]


class PlanningMetricsResponse(BaseModel):
    total_passengers: int
    total_trips: int
    mean_extension_km: float
    total_distance_km: float
    effective_fleet: int
    mean_daily_distance_per_vehicle_km: float
    mean_passengers_per_trip: float
    mean_critical_passengers_per_trip: float
    mean_occupancy_rate: float | None
    passengers_per_km: float
    daily_total_cost: float
    mean_cost_per_vehicle: float
    cost_per_trip: float
    cost_per_equivalent_passenger: float
    mean_trips_per_vehicle: float
    mean_travel_time_min: float
    mean_speed_kmh: float
    distance_semantics: str


class PlanningLineContextResponse(BaseModel):
    public_code: str | None
    name: str


class PlanningResultContextResponse(BaseModel):
    project_id: uuid.UUID
    project_name: str
    scenario_id: uuid.UUID
    scenario_name: str
    scenario_revision_id: uuid.UUID
    scenario_revision_no: int
    lines: list[PlanningLineContextResponse]


class PersistedPlanningResultResponse(BaseModel):
    computation_run_id: uuid.UUID
    plan_revision_id: uuid.UUID
    result_snapshot_id: uuid.UUID
    plan_revision_no: int
    context: PlanningResultContextResponse
    semantic_layer: str
    engine_id: str
    engine_version: str
    input_fingerprint: str
    output_fingerprint: str
    effective_fleet: int
    trips: list[PlannedTripResponse]
    vehicle_blocks: list[VehicleBlockResponse]
    metrics: PlanningMetricsResponse
    provenance_notes: list[str]


router = APIRouter(prefix="/results", tags=["results"])


def _context_for_result(
    session: Session,
    organization_id: uuid.UUID,
    persisted: PersistedPlanningResult,
) -> PlanningResultContextResponse:
    plan = session.execute(
        select(PlanRevision).where(
            PlanRevision.organization_id == organization_id,
            PlanRevision.id == persisted.plan_revision_id,
        )
    ).scalar_one_or_none()
    if plan is None:
        raise PlanningResultIntegrityError("persisted result has no plan revision context")

    row = session.execute(
        select(
            ScenarioRevision.id.label("scenario_revision_id"),
            ScenarioRevision.revision_no.label("scenario_revision_no"),
            Scenario.id.label("scenario_id"),
            Scenario.name.label("scenario_name"),
            PlanningProject.id.label("project_id"),
            PlanningProject.name.label("project_name"),
        )
        .join(
            Scenario,
            and_(
                Scenario.organization_id == ScenarioRevision.organization_id,
                Scenario.id == ScenarioRevision.scenario_id,
            ),
        )
        .join(
            PlanningProject,
            and_(
                PlanningProject.organization_id == Scenario.organization_id,
                PlanningProject.id == Scenario.project_id,
            ),
        )
        .where(
            ScenarioRevision.organization_id == organization_id,
            ScenarioRevision.id == plan.scenario_revision_id,
        )
    ).mappings().one_or_none()
    if row is None:
        raise PlanningResultIntegrityError("persisted result has no project/scenario context")

    line_rows = session.execute(
        select(TransitLine.public_code, TransitLine.name)
        .select_from(ScenarioDirectionPlanningInput)
        .join(
            LineDirection,
            and_(
                LineDirection.organization_id == ScenarioDirectionPlanningInput.organization_id,
                LineDirection.id == ScenarioDirectionPlanningInput.direction_id,
            ),
        )
        .join(
            TransitLine,
            and_(
                TransitLine.organization_id == LineDirection.organization_id,
                TransitLine.id == LineDirection.line_id,
            ),
        )
        .where(
            ScenarioDirectionPlanningInput.organization_id == organization_id,
            ScenarioDirectionPlanningInput.scenario_revision_id == plan.scenario_revision_id,
        )
        .distinct()
        .order_by(TransitLine.public_code, TransitLine.name)
    ).all()

    return PlanningResultContextResponse(
        project_id=row["project_id"],
        project_name=row["project_name"],
        scenario_id=row["scenario_id"],
        scenario_name=row["scenario_name"],
        scenario_revision_id=row["scenario_revision_id"],
        scenario_revision_no=row["scenario_revision_no"],
        lines=[PlanningLineContextResponse(public_code=item.public_code, name=item.name) for item in line_rows],
    )


def _response_for_result(
    session: Session,
    organization_id: uuid.UUID,
    run_id: uuid.UUID,
    persisted: PersistedPlanningResult,
) -> PersistedPlanningResultResponse:
    result = persisted.planning_result
    trips = [
        PlannedTripResponse(
            sequence_no=index,
            direction_key=trip.direction_key,
            legacy_direction_number=trip.legacy_direction_number,
            departure_service_minute=trip.departure_service_minute,
            arrival_service_minute=trip.arrival_service_minute,
            virtual_departure_service_minute=trip.virtual_departure_service_minute,
            virtual_arrival_service_minute=trip.virtual_arrival_service_minute,
            trip_type=trip.trip_type,
            is_express=trip.is_express,
            vehicle_block=trip.vehicle_block,
            service_level=trip.service_level,
        )
        for index, trip in enumerate(result.trips, start=1)
    ]
    blocks = [
        VehicleBlockResponse(
            block_no=block_no,
            trip_sequence_nos=[trip_index + 1 for trip_index in indexes],
        )
        for block_no, indexes in sorted(result.vehicle_blocks.items())
    ]
    return PersistedPlanningResultResponse(
        computation_run_id=run_id,
        plan_revision_id=persisted.plan_revision_id,
        result_snapshot_id=persisted.result_snapshot_id,
        plan_revision_no=persisted.revision_no,
        context=_context_for_result(session, organization_id, persisted),
        semantic_layer=result.semantic_layer.value,
        engine_id=result.engine_id,
        engine_version=result.engine_version,
        input_fingerprint=result.input_fingerprint,
        output_fingerprint=result.output_fingerprint,
        effective_fleet=result.effective_fleet,
        trips=trips,
        vehicle_blocks=blocks,
        metrics=PlanningMetricsResponse(**result.metrics.__dict__),
        provenance_notes=list(result.provenance_notes),
    )


def _load_response(
    session: Session,
    principal: Principal,
    run_id: uuid.UUID,
) -> PersistedPlanningResultResponse:
    try:
        persisted = load_planning_result(principal.organization_id, run_id)
        return _response_for_result(session, principal.organization_id, run_id, persisted)
    except PlanningResultNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PlanningResultIntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/latest", response_model=PersistedPlanningResultResponse)
def get_latest_persisted_result(
    principal: Principal = Depends(require_permission(Permission.RESULT_READ)),
    session: Session = Depends(database_session),
) -> PersistedPlanningResultResponse:
    run_id = session.execute(
        select(PlanRevision.computation_run_id)
        .where(
            PlanRevision.organization_id == principal.organization_id,
            PlanRevision.computation_run_id.is_not(None),
        )
        .order_by(PlanRevision.created_at.desc(), PlanRevision.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    if run_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no persisted planning result exists")
    return _load_response(session, principal, run_id)


@router.get(
    "/computations/{run_id}",
    response_model=PersistedPlanningResultResponse,
)
def get_persisted_result(
    run_id: uuid.UUID,
    principal: Principal = Depends(require_permission(Permission.RESULT_READ)),
    session: Session = Depends(database_session),
) -> PersistedPlanningResultResponse:
    return _load_response(session, principal, run_id)
