from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.orm import Session, aliased

from oferbus_db import (
    LineDirection,
    PlanRevision,
    PlannedTrip,
    ScenarioDirectionPlanningInput,
    Terminal,
    TransitLine,
)

from .identity import Permission, Principal, database_session, require_permission


class MarchTerminalResponse(BaseModel):
    id: uuid.UUID | None
    name: str


class MarchDirectionResponse(BaseModel):
    direction_key: str
    legacy_direction_number: int | None
    line_id: uuid.UUID
    line_public_code: str | None
    line_name: str
    origin: MarchTerminalResponse
    destination: MarchTerminalResponse
    extension_km: float | None


class MarchTripResponse(BaseModel):
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


class MarchPlanResponse(BaseModel):
    plan_revision_id: uuid.UUID
    parent_plan_revision_id: uuid.UUID | None
    scenario_revision_id: uuid.UUID
    revision_no: int
    source_kind: str
    semantic_layer: str
    output_fingerprint: str
    service_start_minute: int
    service_end_minute: int
    directions: list[MarchDirectionResponse]
    trips: list[MarchTripResponse]


router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("/{plan_revision_id}/march", response_model=MarchPlanResponse)
def get_march_plan(
    plan_revision_id: uuid.UUID,
    principal: Principal = Depends(require_permission(Permission.RESULT_READ)),
    session: Session = Depends(database_session),
) -> MarchPlanResponse:
    plan = session.execute(
        select(PlanRevision).where(
            PlanRevision.organization_id == principal.organization_id,
            PlanRevision.id == plan_revision_id,
        )
    ).scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="plan revision not found")

    trips = session.execute(
        select(PlannedTrip)
        .where(
            PlannedTrip.organization_id == principal.organization_id,
            PlannedTrip.plan_revision_id == plan.id,
        )
        .order_by(PlannedTrip.sequence_no)
    ).scalars().all()
    if not trips:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="plan revision has no planned trips")

    origin_terminal = aliased(Terminal)
    destination_terminal = aliased(Terminal)
    direction_rows = session.execute(
        select(
            LineDirection.direction_key,
            LineDirection.legacy_direction_number,
            LineDirection.line_id,
            LineDirection.extension_km,
            TransitLine.public_code.label("line_public_code"),
            TransitLine.name.label("line_name"),
            LineDirection.origin_terminal_id,
            origin_terminal.name.label("origin_terminal_name"),
            LineDirection.destination_terminal_id,
            destination_terminal.name.label("destination_terminal_name"),
        )
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
        .outerjoin(
            origin_terminal,
            and_(
                origin_terminal.organization_id == LineDirection.organization_id,
                origin_terminal.id == LineDirection.origin_terminal_id,
            ),
        )
        .outerjoin(
            destination_terminal,
            and_(
                destination_terminal.organization_id == LineDirection.organization_id,
                destination_terminal.id == LineDirection.destination_terminal_id,
            ),
        )
        .where(
            ScenarioDirectionPlanningInput.organization_id == principal.organization_id,
            ScenarioDirectionPlanningInput.scenario_revision_id == plan.scenario_revision_id,
        )
        .order_by(TransitLine.public_code, TransitLine.name, LineDirection.direction_key)
    ).mappings().all()

    if not direction_rows:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="plan revision has no direction context")

    keys = [str(row["direction_key"]) for row in direction_rows]
    if len(keys) != len(set(keys)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="March Diagram requires unambiguous direction keys; multi-line plan needs explicit trip direction ids",
        )

    direction_keys = set(keys)
    missing = sorted({trip.direction_key for trip in trips} - direction_keys)
    if missing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"planned trips reference directions absent from scenario context: {', '.join(missing)}",
        )

    times = [
        value
        for trip in trips
        for value in (
            trip.departure_service_minute,
            trip.arrival_service_minute,
            trip.virtual_departure_service_minute,
            trip.virtual_arrival_service_minute,
        )
    ]

    directions = [
        MarchDirectionResponse(
            direction_key=str(row["direction_key"]),
            legacy_direction_number=row["legacy_direction_number"],
            line_id=row["line_id"],
            line_public_code=row["line_public_code"],
            line_name=row["line_name"],
            origin=MarchTerminalResponse(
                id=row["origin_terminal_id"],
                name=row["origin_terminal_name"] or "Origem não identificada",
            ),
            destination=MarchTerminalResponse(
                id=row["destination_terminal_id"],
                name=row["destination_terminal_name"] or "Destino não identificado",
            ),
            extension_km=float(row["extension_km"]) if row["extension_km"] is not None else None,
        )
        for row in direction_rows
    ]

    response_trips = [
        MarchTripResponse(
            sequence_no=trip.sequence_no,
            direction_key=trip.direction_key,
            legacy_direction_number=trip.legacy_direction_number,
            departure_service_minute=trip.departure_service_minute,
            arrival_service_minute=trip.arrival_service_minute,
            virtual_departure_service_minute=trip.virtual_departure_service_minute,
            virtual_arrival_service_minute=trip.virtual_arrival_service_minute,
            trip_type=trip.trip_type,
            is_express=trip.is_express,
            vehicle_block=trip.vehicle_block_no,
            service_level=trip.service_level,
        )
        for trip in trips
    ]

    return MarchPlanResponse(
        plan_revision_id=plan.id,
        parent_plan_revision_id=plan.parent_plan_revision_id,
        scenario_revision_id=plan.scenario_revision_id,
        revision_no=plan.revision_no,
        source_kind=plan.source_kind,
        semantic_layer=plan.semantic_layer,
        output_fingerprint=plan.output_fingerprint,
        service_start_minute=min(times),
        service_end_minute=max(times),
        directions=directions,
        trips=response_trips,
    )
