from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from oferbus_db import (
    PlanEditCommand,
    PlanRevision,
    PlannedTrip,
    ScenarioRevision,
    VehicleBlock,
    VehicleBlockTrip,
)

from .audit import record_audit_event
from .identity import Permission, Principal, database_session, require_permission


class ForkPlanRequest(BaseModel):
    client_command_id: uuid.UUID
    command_type: str = Field(pattern="^fork$")
    reason: str = Field(min_length=3, max_length=2000)


class PlanEditResponse(BaseModel):
    command_id: uuid.UUID
    client_command_id: uuid.UUID
    command_type: str
    parent_plan_revision_id: uuid.UUID
    derived_plan_revision_id: uuid.UUID
    derived_revision_no: int
    reason: str


router = APIRouter(prefix="/plans", tags=["plan-editing"])


def _response(command: PlanEditCommand, revision_no: int) -> PlanEditResponse:
    return PlanEditResponse(
        command_id=command.id,
        client_command_id=command.client_command_id,
        command_type=command.command_type,
        parent_plan_revision_id=command.parent_plan_revision_id,
        derived_plan_revision_id=command.derived_plan_revision_id,
        derived_revision_no=revision_no,
        reason=command.reason,
    )


@router.post("/{plan_revision_id}/edits", response_model=PlanEditResponse, status_code=status.HTTP_201_CREATED)
def fork_plan_revision(
    plan_revision_id: uuid.UUID,
    request: ForkPlanRequest,
    principal: Principal = Depends(require_permission(Permission.PLAN_EDIT)),
    session: Session = Depends(database_session),
) -> PlanEditResponse:
    """Create an immutable manual child revision before applying semantic edits.

    C.2 deliberately supports only the typed ``fork`` command. Later C phases add
    domain mutations; accepting arbitrary JSON operations here would bypass the
    semantic and validation boundary.
    """
    existing = session.execute(
        select(PlanEditCommand).where(
            PlanEditCommand.organization_id == principal.organization_id,
            PlanEditCommand.client_command_id == request.client_command_id,
        )
    ).scalar_one_or_none()
    if existing is not None:
        derived_no = session.execute(
            select(PlanRevision.revision_no).where(
                PlanRevision.organization_id == principal.organization_id,
                PlanRevision.id == existing.derived_plan_revision_id,
            )
        ).scalar_one()
        return _response(existing, derived_no)

    parent = session.execute(
        select(PlanRevision).where(
            PlanRevision.organization_id == principal.organization_id,
            PlanRevision.id == plan_revision_id,
        )
    ).scalar_one_or_none()
    if parent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="plan revision not found")

    # Serializes revision-number allocation for this scenario without locking
    # unrelated tenants/scenarios.
    scenario = session.execute(
        select(ScenarioRevision).where(
            ScenarioRevision.organization_id == principal.organization_id,
            ScenarioRevision.id == parent.scenario_revision_id,
        ).with_for_update()
    ).scalar_one()
    next_revision_no = session.execute(
        select(func.coalesce(func.max(PlanRevision.revision_no), 0) + 1).where(
            PlanRevision.organization_id == principal.organization_id,
            PlanRevision.scenario_revision_id == scenario.id,
        )
    ).scalar_one()

    child = PlanRevision(
        organization_id=principal.organization_id,
        scenario_revision_id=parent.scenario_revision_id,
        computation_run_id=None,
        parent_plan_revision_id=parent.id,
        revision_no=next_revision_no,
        source_kind="manual",
        semantic_layer=parent.semantic_layer,
        engine_id=parent.engine_id,
        engine_version=parent.engine_version,
        input_fingerprint=parent.input_fingerprint,
        output_fingerprint=parent.output_fingerprint,
    )
    session.add(child)
    session.flush()

    trip_id_map: dict[uuid.UUID, uuid.UUID] = {}
    parent_trips = session.execute(
        select(PlannedTrip).where(
            PlannedTrip.organization_id == principal.organization_id,
            PlannedTrip.plan_revision_id == parent.id,
        ).order_by(PlannedTrip.sequence_no)
    ).scalars().all()
    for trip in parent_trips:
        clone = PlannedTrip(
            organization_id=principal.organization_id,
            plan_revision_id=child.id,
            sequence_no=trip.sequence_no,
            direction_key=trip.direction_key,
            legacy_direction_number=trip.legacy_direction_number,
            departure_service_minute=trip.departure_service_minute,
            arrival_service_minute=trip.arrival_service_minute,
            virtual_departure_service_minute=trip.virtual_departure_service_minute,
            virtual_arrival_service_minute=trip.virtual_arrival_service_minute,
            trip_type=trip.trip_type,
            is_express=trip.is_express,
            vehicle_block_no=trip.vehicle_block_no,
            service_level=trip.service_level,
        )
        session.add(clone)
        session.flush()
        trip_id_map[trip.id] = clone.id

    blocks = session.execute(
        select(VehicleBlock).where(
            VehicleBlock.organization_id == principal.organization_id,
            VehicleBlock.plan_revision_id == parent.id,
        ).order_by(VehicleBlock.block_no)
    ).scalars().all()
    for block in blocks:
        session.add(VehicleBlock(
            organization_id=principal.organization_id,
            plan_revision_id=child.id,
            block_no=block.block_no,
            trip_count=block.trip_count,
            first_departure_service_minute=block.first_departure_service_minute,
            last_arrival_service_minute=block.last_arrival_service_minute,
        ))
    session.flush()

    links = session.execute(
        select(VehicleBlockTrip).where(
            VehicleBlockTrip.organization_id == principal.organization_id,
            VehicleBlockTrip.plan_revision_id == parent.id,
        ).order_by(VehicleBlockTrip.block_no, VehicleBlockTrip.position_no)
    ).scalars().all()
    for link in links:
        session.add(VehicleBlockTrip(
            organization_id=principal.organization_id,
            plan_revision_id=child.id,
            block_no=link.block_no,
            position_no=link.position_no,
            planned_trip_id=trip_id_map[link.planned_trip_id],
        ))

    command = PlanEditCommand(
        organization_id=principal.organization_id,
        client_command_id=request.client_command_id,
        parent_plan_revision_id=parent.id,
        derived_plan_revision_id=child.id,
        command_type="fork",
        payload={},
        reason=request.reason,
        created_by=principal.user_id,
    )
    session.add(command)
    record_audit_event(
        session,
        principal,
        event_type="plan.revision.forked",
        entity_type="plan_revision",
        entity_id=child.id,
        correlation_id=str(request.client_command_id),
        details={
            "parent_plan_revision_id": str(parent.id),
            "derived_revision_no": next_revision_no,
            "command_type": "fork",
            "reason": request.reason,
        },
    )
    session.commit()
    return _response(command, next_revision_no)
