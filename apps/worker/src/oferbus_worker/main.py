from __future__ import annotations

import os
import socket
import time

from oferbus_jobs import PostgresComputationQueue, RunSnapshot

POLL_INTERVAL_SECONDS = float(os.getenv("OFERBUS_WORKER_POLL_SECONDS", "1.0"))
LEASE_SECONDS = int(os.getenv("OFERBUS_WORKER_LEASE_SECONDS", "60"))


def worker_id() -> str:
    configured = os.getenv("OFERBUS_WORKER_ID")
    if configured:
        return configured
    return f"{socket.gethostname()}:{os.getpid()}"


def platform_smoke(run: RunSnapshot, queue: PostgresComputationQueue, owner: str) -> dict[str, object]:
    delay = run.payload.get("delay_seconds", 0.2)
    try:
        delay_seconds = min(3.0, max(0.0, float(delay)))
    except (TypeError, ValueError):
        delay_seconds = 0.2

    queue.heartbeat(run.run_id, owner, progress_percent=25, lease_seconds=LEASE_SECONDS)
    time.sleep(delay_seconds / 2)
    queue.heartbeat(run.run_id, owner, progress_percent=75, lease_seconds=LEASE_SECONDS)
    time.sleep(delay_seconds / 2)

    return {
        "handler": "platform-smoke",
        "message": run.payload.get("message", "OferBus async boundary is operational"),
        "worker_id": owner,
    }


HANDLERS = {
    "platform-smoke": platform_smoke,
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
        diagnostics = handler(run, queue, owner)
    except Exception as exc:  # worker boundary must persist failure rather than crash the process
        queue.fail(run.run_id, owner, f"{type(exc).__name__}: {exc}", retryable=True)
        return True

    queue.succeed(run.run_id, owner, diagnostics=diagnostics)
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
