from __future__ import annotations

import os
import socket
import time
from dataclasses import asdict, dataclass

from oferbus_core import ENGINE_ID, ENGINE_VERSION, ReferencePlanningAdapter, fingerprint
from oferbus_jobs import PostgresComputationQueue, RunSnapshot
from oferbus_planning import PlanningInputError, load_planning_input

POLL_INTERVAL_SECONDS = float(os.getenv("OFERBUS_WORKER_POLL_SECONDS", "1.0"))
LEASE_SECONDS = int(os.getenv("OFERBUS_WORKER_LEASE_SECONDS", "60"))
CORE_ENGINE_DESCRIPTOR = f"{ENGINE_ID}:{ENGINE_VERSION}"


@dataclass(frozen=True)
class HandlerOutcome:
    diagnostics: dict[str, object]
    output_fingerprint: str | None = None


class NonRetryableJobError(RuntimeError):
    """Deterministic job error that retrying cannot repair."""


def worker_id() -> str:
    configured = os.getenv("OFERBUS_WORKER_ID")
    if configured:
        return configured
    return f"{socket.gethostname()}:{os.getpid()}"


def platform_smoke(run: RunSnapshot, queue: PostgresComputationQueue, owner: str) -> HandlerOutcome:
    delay = run.payload.get("delay_seconds", 0.2)
    try:
        delay_seconds = min(3.0, max(0.0, float(delay)))
    except (TypeError, ValueError):
        delay_seconds = 0.2

    queue.heartbeat(run.run_id, owner, progress_percent=25, lease_seconds=LEASE_SECONDS)
    time.sleep(delay_seconds / 2)
    queue.heartbeat(run.run_id, owner, progress_percent=75, lease_seconds=LEASE_SECONDS)
    time.sleep(delay_seconds / 2)

    return HandlerOutcome(
        diagnostics={
            "handler": "platform-smoke",
            "message": run.payload.get("message", "OferBus async boundary is operational"),
            "worker_id": owner,
        }
    )


def core_planning(run: RunSnapshot, queue: PostgresComputationQueue, owner: str) -> HandlerOutcome:
    if run.engine_version != CORE_ENGINE_DESCRIPTOR:
        raise NonRetryableJobError(
            f"queued engine {run.engine_version!r} does not match worker engine {CORE_ENGINE_DESCRIPTOR!r}"
        )
    if run.input_fingerprint is None:
        raise NonRetryableJobError("core-planning run has no input fingerprint")

    queue.heartbeat(run.run_id, owner, progress_percent=10, lease_seconds=LEASE_SECONDS)
    try:
        planning_input = load_planning_input(run.organization_id, run.scenario_revision_id)
    except PlanningInputError as exc:
        raise NonRetryableJobError(f"planning input cannot be loaded: {exc}") from exc

    actual_input_fingerprint = fingerprint(planning_input)
    if actual_input_fingerprint != run.input_fingerprint:
        raise NonRetryableJobError("queued input fingerprint does not match immutable scenario snapshot")
    if planning_input.semantic_layer.value != run.semantic_layer:
        raise NonRetryableJobError("queued semantic layer does not match immutable scenario snapshot")

    queue.heartbeat(run.run_id, owner, progress_percent=35, lease_seconds=LEASE_SECONDS)
    try:
        result = ReferencePlanningAdapter().execute(planning_input)
    except (ValueError, NotImplementedError, ZeroDivisionError) as exc:
        raise NonRetryableJobError(f"deterministic planning failed: {type(exc).__name__}: {exc}") from exc

    if result.input_fingerprint != run.input_fingerprint:
        raise NonRetryableJobError("planning engine returned a different input fingerprint")
    if result.engine_id != ENGINE_ID or result.engine_version != ENGINE_VERSION:
        raise NonRetryableJobError("planning engine provenance does not match worker engine")

    queue.heartbeat(run.run_id, owner, progress_percent=85, lease_seconds=LEASE_SECONDS)

    metrics = asdict(result.metrics)
    diagnostics: dict[str, object] = {
        "handler": "core-planning",
        "worker_id": owner,
        "engine_id": result.engine_id,
        "engine_version": result.engine_version,
        "semantic_layer": result.semantic_layer.value,
        "input_fingerprint": result.input_fingerprint,
        "output_fingerprint": result.output_fingerprint,
        "trip_count": len(result.trips),
        "effective_fleet": result.effective_fleet,
        "total_passengers": metrics["total_passengers"],
        "total_distance_km": metrics["total_distance_km"],
        "daily_total_cost": metrics["daily_total_cost"],
        "provenance_notes": list(result.provenance_notes),
        "result_persistence": "deferred-to-phase-b4",
    }
    return HandlerOutcome(diagnostics=diagnostics, output_fingerprint=result.output_fingerprint)


HANDLERS = {
    "platform-smoke": platform_smoke,
    "core-planning": core_planning,
}


def process_one(queue: PostgresComputationQueue, owner: str) -> bool:
    run = queue.claim(owner, lease_seconds=LEASE_SECONDS)
    if run is None:
        return False

    handler = HANDLERS.get(run.run_kind)
    if handler is None:
        queue.fail(run.run_id, owner, f"No worker handler registered for run_kind={run.run_kind}", retryable=False)
        return True

    try:
        outcome = handler(run, queue, owner)
    except NonRetryableJobError as exc:
        queue.fail(run.run_id, owner, str(exc), retryable=False)
        return True
    except Exception as exc:  # transient infrastructure errors remain retryable at the worker boundary
        queue.fail(run.run_id, owner, f"{type(exc).__name__}: {exc}", retryable=True)
        return True

    queue.succeed(
        run.run_id,
        owner,
        diagnostics=outcome.diagnostics,
        output_fingerprint=outcome.output_fingerprint,
    )
    return True


def main() -> None:
    queue = PostgresComputationQueue()
    owner = worker_id()
    print(f"OferBus worker started: {owner}", flush=True)

    while True:
        processed = process_one(queue, owner)
        if not processed:
            time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
