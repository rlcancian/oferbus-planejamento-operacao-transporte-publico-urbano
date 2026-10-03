from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from oferbus_db import PlanRevision, PlannedTrip, ResultSnapshot, VehicleBlock

from .identity import Permission, Principal, database_session, require_permission


class ResultFreshnessResponse(BaseModel):
    plan_revision_id: uuid.UUID
    parent_plan_revision_id: uuid.UUID | None
    source_kind: str
    status: Literal["fresh", "needs-recalculation"]
    inherited_parent_result_status: Literal["not-applicable", "stale"]
    result_snapshot_id: uuid.UUID | None
    reason: str


class TripChange(BaseModel):
    sequence_no: int
    changed_fields: list[str]


class BlockChange(BaseModel):
    block_no: int
    changed_fields: list[str]


class PlanRevisionComparisonResponse(BaseModel):
    parent_plan_revision_id: uuid.UUID
    child_plan_revision_id: uuid.UUID
    parent_revision_no: int
    child_revision_no: int
    semantic_layer: str
    changed_trip_count: int
    changed_block_count: int
    trip_changes: list[TripChange]
    block_changes: list[BlockChange]
    child_result_status: Literal["fresh", "needs-recalculation"]


router = APIRouter(prefix="/plans", tags=["plan-results"])


def _plan(session: Session, organization_id: uuid.UUID, plan_revision_id: uuid.UUID) -> PlanRevision:
    plan = session.execute(
        select(PlanRevision).where(
            PlanRevision.organization_id == organization_id,
            PlanRevision.id == plan_revision_id,
        )
    ).scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="plan revision not found")
    return plan


def _snapshot(session: Session, organization_id: uuid.UUID, plan_revision_id: uuid.UUID) -> ResultSnapshot | None:
    return session.execute(
        select(ResultSnapshot).where(
            ResultSnapshot.organization_id == organization_id,
            ResultSnapshot.plan_revision_id == plan_revision_id,
        )
    ).scalar_one_or_none()


def _freshness(session: Session, organization_id: uuid.UUID, plan: PlanRevision) -> ResultFreshnessResponse:
    snapshot = _snapshot(session, organization_id, plan.id)
    if snapshot is not None:
        return ResultFreshnessResponse(
            plan_revision_id=plan.id,
            parent_plan_revision_id=plan.parent_plan_revision_id,
            source_kind=plan.source_kind,
            status="fresh",
            inherited_parent_result_status="not-applicable",
            result_snapshot_id=snapshot.id,
            reason="a persisted result snapshot belongs to this exact immutable plan revision",
        )
    return ResultFreshnessResponse(
        plan_revision_id=plan.id,
        parent_plan_revision_id=plan.parent_plan_revision_id,
        source_kind=plan.source_kind,
        status="needs-recalculation",
        inherited_parent_result_status="stale" if plan.parent_plan_revision_id is not None else "not-applicable",
        result_snapshot_id=None,
        reason=(
            "no result snapshot exists for this exact revision; parent metrics, when present, are stale and are not promoted to the child"
        ),
    )


@router.get("/{plan_revision_id}/result-status", response_model=ResultFreshnessResponse)
def get_plan_result_status(
    plan_revision_id: uuid.UUID,
    principal: Principal = Depends(require_permission(Permission.RESULT_READ)),
    session: Session = Depends(database_session),
) -> ResultFreshnessResponse:
    """Report result validity without pretending that parent metrics were recalculated."""
    return _freshness(session, principal.organization_id, _plan(session, principal.organization_id, plan_revision_id))


@router.get("/{plan_revision_id}/compare-parent", response_model=PlanRevisionComparisonResponse)
def compare_plan_with_parent(
    plan_revision_id: uuid.UUID,
    principal: Principal = Depends(require_permission(Permission.RESULT_READ)),
    session: Session = Depends(database_session),
) -> PlanRevisionComparisonResponse:
    """Compare persisted operational state of one immutable child revision with its direct parent."""
    child = _plan(session, principal.organization_id, plan_revision_id)
    if child.parent_plan_revision_id is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="plan revision has no parent")
    parent = _plan(session, principal.organization_id, child.parent_plan_revision_id)

    parent_trips = {
        trip.sequence_no: trip
        for trip in session.execute(
            select(PlannedTrip).where(
                PlannedTrip.organization_id == principal.organization_id,
                PlannedTrip.plan_revision_id == parent.id,
            )
        ).scalars()
    }
    child_trips = {
        trip.sequence_no: trip
        for trip in session.execute(
            select(PlannedTrip).where(
                PlannedTrip.organization_id == principal.organization_id,
                PlannedTrip.plan_revision_id == child.id,
            )
        ).scalars()
    }
    trip_fields = (
        "direction_key",
        "legacy_direction_number",
        "departure_service_minute",
        "arrival_service_minute",
        "virtual_departure_service_minute",
        "virtual_arrival_service_minute",
        "trip_type",
        "is_express",
        "vehicle_block_no",
        "service_level",
    )
    trip_changes: list[TripChange] = []
    for sequence_no in sorted(set(parent_trips) | set(child_trips)):
        before = parent_trips.get(sequence_no)
        after = child_trips.get(sequence_no)
        if before is None or after is None:
            changed = ["created"] if before is None else ["removed"]
        else:
            changed = [field for field in trip_fields if getattr(before, field) != getattr(after, field)]
        if changed:
            trip_changes.append(TripChange(sequence_no=sequence_no, changed_fields=changed))

    parent_blocks = {
        block.block_no: block
        for block in session.execute(
            select(VehicleBlock).where(
                VehicleBlock.organization_id == principal.organization_id,
                VehicleBlock.plan_revision_id == parent.id,
            )
        ).scalars()
    }
    child_blocks = {
        block.block_no: block
        for block in session.execute(
            select(VehicleBlock).where(
                VehicleBlock.organization_id == principal.organization_id,
                VehicleBlock.plan_revision_id == child.id,
            )
        ).scalars()
    }
    block_fields = ("trip_count", "first_departure_service_minute", "last_arrival_service_minute")
    block_changes: list[BlockChange] = []
    for block_no in sorted(set(parent_blocks) | set(child_blocks)):
        before = parent_blocks.get(block_no)
        after = child_blocks.get(block_no)
        if before is None or after is None:
            changed = ["created"] if before is None else ["removed"]
        else:
            changed = [field for field in block_fields if getattr(before, field) != getattr(after, field)]
        if changed:
            block_changes.append(BlockChange(block_no=block_no, changed_fields=changed))

    freshness = _freshness(session, principal.organization_id, child)
    return PlanRevisionComparisonResponse(
        parent_plan_revision_id=parent.id,
        child_plan_revision_id=child.id,
        parent_revision_no=parent.revision_no,
        child_revision_no=child.revision_no,
        semantic_layer=child.semantic_layer,
        changed_trip_count=len(trip_changes),
        changed_block_count=len(block_changes),
        trip_changes=trip_changes,
        block_changes=block_changes,
        child_result_status=freshness.status,
    )
