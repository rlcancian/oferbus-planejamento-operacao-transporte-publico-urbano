from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from oferbus_db import PlanEditCommand, PlanRevision

from .identity import Permission, Principal, database_session, require_permission


class RevisionHistoryEntry(BaseModel):
    plan_revision_id: uuid.UUID
    revision_no: int
    parent_plan_revision_id: uuid.UUID | None
    source_kind: str
    command_type: str | None = None
    reason: str | None = None
    created_by: uuid.UUID | None = None


class RevisionHistoryResponse(BaseModel):
    current_plan_revision_id: uuid.UUID
    ancestors: list[RevisionHistoryEntry]
    redo_candidates: list[RevisionHistoryEntry]


router = APIRouter(prefix="/plans", tags=["plan-history"])


def _entry(session: Session, principal: Principal, revision: PlanRevision) -> RevisionHistoryEntry:
    command = session.execute(
        select(PlanEditCommand).where(
            PlanEditCommand.organization_id == principal.organization_id,
            PlanEditCommand.derived_plan_revision_id == revision.id,
        )
    ).scalar_one_or_none()
    return RevisionHistoryEntry(
        plan_revision_id=revision.id,
        revision_no=revision.revision_no,
        parent_plan_revision_id=revision.parent_plan_revision_id,
        source_kind=revision.source_kind,
        command_type=command.command_type if command else None,
        reason=command.reason if command else None,
        created_by=command.created_by if command else None,
    )


@router.get("/{plan_revision_id}/history", response_model=RevisionHistoryResponse)
def revision_history(
    plan_revision_id: uuid.UUID,
    principal: Principal = Depends(require_permission(Permission.RESULT_READ)),
    session: Session = Depends(database_session),
) -> RevisionHistoryResponse:
    """Return safe undo ancestry and explicit redo branches without mutating history."""
    current = session.execute(
        select(PlanRevision).where(
            PlanRevision.organization_id == principal.organization_id,
            PlanRevision.id == plan_revision_id,
        )
    ).scalar_one_or_none()
    if current is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="plan revision not found")

    ancestors: list[RevisionHistoryEntry] = []
    cursor = current
    seen: set[uuid.UUID] = set()
    while cursor.parent_plan_revision_id is not None:
        if cursor.id in seen:
            raise HTTPException(status_code=409, detail="revision lineage cycle detected")
        seen.add(cursor.id)
        parent = session.execute(
            select(PlanRevision).where(
                PlanRevision.organization_id == principal.organization_id,
                PlanRevision.id == cursor.parent_plan_revision_id,
            )
        ).scalar_one_or_none()
        if parent is None:
            raise HTTPException(status_code=409, detail="revision lineage is incomplete")
        ancestors.append(_entry(session, principal, parent))
        cursor = parent

    children = session.execute(
        select(PlanRevision)
        .where(
            PlanRevision.organization_id == principal.organization_id,
            PlanRevision.parent_plan_revision_id == current.id,
        )
        .order_by(PlanRevision.revision_no)
    ).scalars().all()

    return RevisionHistoryResponse(
        current_plan_revision_id=current.id,
        ancestors=ancestors,
        redo_candidates=[_entry(session, principal, child) for child in children],
    )
