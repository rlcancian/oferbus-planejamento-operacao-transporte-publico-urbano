from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from oferbus_planning import (
    PlanningResultIntegrityError,
    PlanningResultNotFound,
    load_planning_result,
)

from .identity import Permission, Principal, require_permission


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


class PersistedPlanningResultResponse(BaseModel):
    computation_run_id: uuid.UUID
    plan_revision_id: uuid.UUID
    result_snapshot_id: uuid.UUID
    plan_revision_no: int
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


@router.get(
    "/computations/{run_id}",
    response_model=PersistedPlanningResultResponse,
)
def get_persisted_result(
    run_id: uuid.UUID,
    principal: Principal = Depends(require_permission(Permission.RESULT_READ)),
) -> PersistedPlanningResultResponse:
    try:
        persisted = load_planning_result(principal.organization_id, run_id)
    except PlanningResultNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PlanningResultIntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

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
