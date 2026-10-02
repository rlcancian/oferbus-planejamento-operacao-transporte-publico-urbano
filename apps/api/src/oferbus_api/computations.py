from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError

from oferbus_core import ENGINE_ID, ENGINE_VERSION, fingerprint
from oferbus_jobs import (
    TERMINAL_STATUSES,
    IdempotencyConflictError,
    PostgresComputationQueue,
    RunSnapshot,
    RunSubmission,
)
from oferbus_planning import PlanningInputError, PlanningInputIntegrityError, PlanningInputNotFound, load_planning_input

from .identity import Permission, Principal, require_permission

CORE_ENGINE_DESCRIPTOR = f"{ENGINE_ID}:{ENGINE_VERSION}"


class ComputationSubmitRequest(BaseModel):
    scenario_revision_id: uuid.UUID
    run_kind: Literal["platform-smoke", "core-planning"] = "core-planning"
    semantic_layer: Literal["legacy-exact", "normalized", "modern"] | None = None
    idempotency_key: str | None = Field(default=None, max_length=160)
    payload: dict[str, Any] = Field(default_factory=dict)
    max_attempts: int = Field(default=3, ge=1, le=10)


class ComputationRunResponse(BaseModel):
    run_id: uuid.UUID
    organization_id: uuid.UUID
    scenario_revision_id: uuid.UUID
    run_kind: str
    semantic_layer: str
    engine_version: str
    status: str
    input_fingerprint: str | None
    output_fingerprint: str | None
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
        scenario_revision_id=snapshot.scenario_revision_id,
        run_kind=snapshot.run_kind,
        semantic_layer=snapshot.semantic_layer,
        engine_version=snapshot.engine_version,
        status=snapshot.status,
        input_fingerprint=snapshot.input_fingerprint,
        output_fingerprint=snapshot.output_fingerprint,
        progress_percent=snapshot.progress_percent,
        attempt_count=snapshot.attempt_count,
        max_attempts=snapshot.max_attempts,
        queued_at=snapshot.queued_at.isoformat(),
        started_at=snapshot.started_at.isoformat() if snapshot.started_at else None,
        completed_at=snapshot.completed_at.isoformat() if snapshot.completed_at else None,
        last_error=snapshot.last_error,
        diagnostics=snapshot.diagnostics,
    )


def _planning_http_error(exc: PlanningInputError) -> HTTPException:
    if isinstance(exc, PlanningInputNotFound):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, PlanningInputIntegrityError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


def _submission(request: ComputationSubmitRequest, principal: Principal) -> RunSubmission:
    if request.run_kind == "platform-smoke":
        if request.semantic_layer not in {None, "modern"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="platform-smoke only accepts semantic_layer=modern",
            )
        return RunSubmission(
            organization_id=principal.organization_id,
            scenario_revision_id=request.scenario_revision_id,
            submitted_by=principal.user_id,
            run_kind="platform-smoke",
            semantic_layer="modern",
            engine_version="phase-a4-smoke-1",
            idempotency_key=request.idempotency_key,
            payload=request.payload,
            max_attempts=request.max_attempts,
        )

    if request.payload:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="core-planning accepts no ad-hoc payload; all scientific input comes from the immutable scenario revision",
        )

    try:
        planning_input = load_planning_input(principal.organization_id, request.scenario_revision_id)
    except PlanningInputError as exc:
        raise _planning_http_error(exc) from exc

    semantic_layer = planning_input.semantic_layer.value
    if request.semantic_layer is not None and request.semantic_layer != semantic_layer:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="requested semantic layer does not match the immutable scenario revision",
        )

    return RunSubmission(
        organization_id=principal.organization_id,
        scenario_revision_id=request.scenario_revision_id,
        submitted_by=principal.user_id,
        run_kind="core-planning",
        semantic_layer=semantic_layer,
        engine_version=CORE_ENGINE_DESCRIPTOR,
        input_fingerprint=fingerprint(planning_input),
        idempotency_key=request.idempotency_key,
        payload={},
        max_attempts=request.max_attempts,
    )


router = APIRouter(prefix="/computations", tags=["computations"])


@router.post("", response_model=ComputationRunResponse, status_code=status.HTTP_202_ACCEPTED)
def submit_computation(
    request: ComputationSubmitRequest,
    principal: Principal = Depends(require_permission(Permission.COMPUTATION_RUN)),
) -> ComputationRunResponse:
    queue = PostgresComputationQueue()
    try:
        snapshot = queue.submit(_submission(request, principal))
    except IdempotencyConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
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
