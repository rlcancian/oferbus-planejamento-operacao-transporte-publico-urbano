from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError

from oferbus_jobs import PostgresComputationQueue, RunSnapshot, RunSubmission, TERMINAL_STATUSES

from .identity import Permission, Principal, require_permission


class ComputationSubmitRequest(BaseModel):
    scenario_revision_id: uuid.UUID
    run_kind: Literal["platform-smoke"] = "platform-smoke"
    semantic_layer: Literal["modern"] = "modern"
    idempotency_key: str | None = Field(default=None, max_length=160)
    payload: dict[str, Any] = Field(default_factory=dict)
    max_attempts: int = Field(default=3, ge=1, le=10)


class ComputationRunResponse(BaseModel):
    run_id: uuid.UUID
    organization_id: uuid.UUID
    run_kind: str
    semantic_layer: str
    status: str
    progress_percent: int
    attempt_count: int
    max_attempts: int
    queued_at: str
    started_at: str | None
    completed_at: str | None
    last_error: str | None
    diagnostics: dict[str, Any] | None


def _response(snapshot: RunSnapshot) -> ComputationRunResponse:
    return ComputationRunResponse(
        run_id=snapshot.run_id,
        organization_id=snapshot.organization_id,
        run_kind=snapshot.run_kind,
        semantic_layer=snapshot.semantic_layer,
        status=snapshot.status,
        progress_percent=snapshot.progress_percent,
        attempt_count=snapshot.attempt_count,
        max_attempts=snapshot.max_attempts,
        queued_at=snapshot.queued_at.isoformat(),
        started_at=snapshot.started_at.isoformat() if snapshot.started_at else None,
        completed_at=snapshot.completed_at.isoformat() if snapshot.completed_at else None,
        last_error=snapshot.last_error,
        diagnostics=snapshot.diagnostics,
    )


router = APIRouter(prefix="/computations", tags=["computations"])


@router.post("", response_model=ComputationRunResponse, status_code=status.HTTP_202_ACCEPTED)
def submit_computation(
    request: ComputationSubmitRequest,
    principal: Principal = Depends(require_permission(Permission.COMPUTATION_RUN)),
) -> ComputationRunResponse:
    queue = PostgresComputationQueue()
    try:
        snapshot = queue.submit(
            RunSubmission(
                organization_id=principal.organization_id,
                scenario_revision_id=request.scenario_revision_id,
                submitted_by=principal.user_id,
                run_kind=request.run_kind,
                semantic_layer=request.semantic_layer,
                engine_version="phase-a4-smoke-1",
                idempotency_key=request.idempotency_key,
                payload=request.payload,
                max_attempts=request.max_attempts,
            )
        )
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Computation could not be queued for the selected scenario revision",
        ) from exc

    return _response(snapshot)


@router.get("/{run_id}", response_model=ComputationRunResponse)
def get_computation(
    run_id: uuid.UUID,
    principal: Principal = Depends(require_permission(Permission.RESULT_READ)),
) -> ComputationRunResponse:
    snapshot = PostgresComputationQueue().get(principal.organization_id, run_id)
    if snapshot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Computation run not found")
    return _response(snapshot)


@router.get("/{run_id}/events")
async def computation_events(
    run_id: uuid.UUID,
    principal: Principal = Depends(require_permission(Permission.RESULT_READ)),
) -> StreamingResponse:
    queue = PostgresComputationQueue()
    initial = await asyncio.to_thread(queue.get, principal.organization_id, run_id)
    if initial is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Computation run not found")

    async def stream():
        last_signature: tuple[str, int, int] | None = None
        while True:
            snapshot = await asyncio.to_thread(queue.get, principal.organization_id, run_id)
            if snapshot is None:
                yield "event: error\ndata: {\"detail\":\"run-not-found\"}\n\n"
                return

            signature = (snapshot.status, snapshot.progress_percent, snapshot.attempt_count)
            if signature != last_signature:
                payload = _response(snapshot).model_dump(mode="json")
                yield f"event: computation\ndata: {json.dumps(payload, separators=(',', ':'))}\n\n"
                last_signature = signature

            if snapshot.status in TERMINAL_STATUSES:
                return

            await asyncio.sleep(1)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
