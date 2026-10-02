import uuid
from datetime import UTC, datetime

from oferbus_jobs import RunSnapshot
from oferbus_worker.main import process_one


class FakeQueue:
    def __init__(self) -> None:
        self.run = RunSnapshot(
            run_id=uuid.uuid4(),
            organization_id=uuid.uuid4(),
            run_kind="platform-smoke",
            semantic_layer="modern",
            status="queued",
            payload={"delay_seconds": 0, "message": "ok"},
            progress_percent=0,
            attempt_count=0,
            max_attempts=3,
            queued_at=datetime.now(UTC),
            started_at=None,
            completed_at=None,
            last_error=None,
            diagnostics=None,
        )
        self.heartbeats: list[int | None] = []
        self.succeeded: dict | None = None
        self.failed: str | None = None

    def claim(self, worker_id: str, lease_seconds: int = 60):
        run, self.run = self.run, None
        return run

    def heartbeat(self, run_id, worker_id, progress_percent=None, lease_seconds=60):
        self.heartbeats.append(progress_percent)

    def succeed(self, run_id, worker_id, diagnostics=None):
        self.succeeded = diagnostics

    def fail(self, run_id, worker_id, error, retryable=True):
        self.failed = error


def test_platform_smoke_job_reports_progress_and_completes() -> None:
    queue = FakeQueue()

    processed = process_one(queue, "test-worker")

    assert processed is True
    assert queue.heartbeats == [25, 75]
    assert queue.failed is None
    assert queue.succeeded is not None
    assert queue.succeeded["handler"] == "platform-smoke"
    assert queue.succeeded["message"] == "ok"
