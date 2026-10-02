import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from oferbus_core import (
    CostPlanningInput,
    DirectionPlanningInput,
    ObservedTripInput,
    PlanningInput,
    PlanningSpecification,
    SemanticLayer,
    VehiclePlanningInput,
    fingerprint,
)
from oferbus_jobs import RunSnapshot
from oferbus_worker import main as worker_main


class FakeQueue:
    def __init__(self, run: RunSnapshot) -> None:
        self.run = run
        self.heartbeats: list[int | None] = []
        self.succeeded: dict | None = None
        self.output_fingerprint: str | None = None
        self.failed: str | None = None
        self.retryable: bool | None = None

    def claim(self, worker_id: str, lease_seconds: int = 60):
        run, self.run = self.run, None
        return run

    def heartbeat(self, run_id, worker_id, progress_percent=None, lease_seconds=60):
        self.heartbeats.append(progress_percent)

    def succeed(self, run_id, worker_id, diagnostics=None, output_fingerprint=None):
        self.succeeded = diagnostics
        self.output_fingerprint = output_fingerprint

    def fail(self, run_id, worker_id, error, retryable=True):
        self.failed = error
        self.retryable = retryable


def _run(**overrides) -> RunSnapshot:
    values = dict(
        run_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        scenario_revision_id=uuid.uuid4(),
        run_kind="platform-smoke",
        semantic_layer="modern",
        engine_version="phase-a4-smoke-1",
        engine_source_revision=None,
        deterministic_seed=None,
        status="queued",
        input_fingerprint=None,
        output_fingerprint=None,
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
    values.update(overrides)
    return RunSnapshot(**values)


def _planning_input() -> PlanningInput:
    start, end = 60, 120
    service_minutes = end - start + 1
    return PlanningInput(
        semantic_layer=SemanticLayer.NORMALIZED,
        directions=(
            DirectionPlanningInput(
                direction_key="outbound",
                legacy_direction_number=1,
                observations=(
                    ObservedTripInput(60, 10, critical_passengers=10, travel_time_min=10),
                    ObservedTripInput(90, 10, critical_passengers=10, travel_time_min=10),
                    ObservedTripInput(120, 10, critical_passengers=10, travel_time_min=10),
                ),
                demand_passengers_per_minute=tuple([0.0] + [1.0] * service_minutes + [0.0]),
                renewal_index_curve=tuple([0.0] + [1.0] * service_minutes + [0.0]),
                travel_time_min_curve=tuple([0.0] + [10.0] * service_minutes + [0.0]),
                service_start_minute=start,
                service_end_minute=end,
                demand_maximum_passengers_per_minute=1.0,
                extension_km=8.0,
                storage_at_departure_terminal=True,
            ),
        ),
        vehicle=VehiclePlanningInput(seats=20, free_area_m2=10.0, capacity_level=1),
        cost=CostPlanningInput(mode="per_km", cost_per_km=2.0),
        specification=PlanningSpecification(
            max_headway_min=20,
            project_capacity_passengers=10.0,
            valley_capacity_passengers=10.0,
            boarding_seconds_per_passenger=0.0,
            alighting_seconds_per_passenger=0.0,
            radial=False,
        ),
    )


def test_platform_smoke_job_reports_progress_and_completes() -> None:
    queue = FakeQueue(_run())

    processed = worker_main.process_one(queue, "test-worker")

    assert processed is True
    assert queue.heartbeats == [25, 75]
    assert queue.failed is None
    assert queue.succeeded is not None
    assert queue.succeeded["handler"] == "platform-smoke"
    assert queue.succeeded["message"] == "ok"
    assert queue.output_fingerprint is None


def test_core_planning_executes_real_adapter_and_persists_fingerprints(monkeypatch) -> None:
    planning_input = _planning_input()
    input_fingerprint = fingerprint(planning_input)
    run = _run(
        run_kind="core-planning",
        semantic_layer="normalized",
        engine_version=worker_main.CORE_ENGINE_DESCRIPTOR,
        input_fingerprint=input_fingerprint,
        payload={},
    )
    queue = FakeQueue(run)
    plan_revision_id = uuid.uuid4()
    result_snapshot_id = uuid.uuid4()
    persisted_call: dict[str, object] = {}

    monkeypatch.setattr(worker_main, "load_planning_input", lambda organization_id, scenario_revision_id: planning_input)

    def fake_persist(organization_id, computation_run_id, result):
        persisted_call.update(
            organization_id=organization_id,
            computation_run_id=computation_run_id,
            output_fingerprint=result.output_fingerprint,
        )
        return SimpleNamespace(
            plan_revision_id=plan_revision_id,
            result_snapshot_id=result_snapshot_id,
            revision_no=1,
        )

    monkeypatch.setattr(worker_main, "persist_planning_result", fake_persist)

    processed = worker_main.process_one(queue, "planning-worker")

    assert processed is True
    assert queue.failed is None
    assert queue.heartbeats == [10, 35, 85, 95]
    assert queue.succeeded is not None
    assert queue.succeeded["handler"] == "core-planning"
    assert queue.succeeded["semantic_layer"] == "normalized"
    assert queue.succeeded["trip_count"] > 0
    assert queue.succeeded["effective_fleet"] >= 1
    assert queue.succeeded["input_fingerprint"] == input_fingerprint
    assert isinstance(queue.output_fingerprint, str) and len(queue.output_fingerprint) == 64
    assert queue.succeeded["output_fingerprint"] == queue.output_fingerprint
    assert queue.succeeded["result_persistence"] == "persisted"
    assert queue.succeeded["plan_revision_id"] == str(plan_revision_id)
    assert queue.succeeded["result_snapshot_id"] == str(result_snapshot_id)
    assert queue.succeeded["plan_revision_no"] == 1
    assert persisted_call == {
        "organization_id": run.organization_id,
        "computation_run_id": run.run_id,
        "output_fingerprint": queue.output_fingerprint,
    }


def test_core_planning_rejects_snapshot_fingerprint_mismatch_without_retry(monkeypatch) -> None:
    planning_input = _planning_input()
    run = _run(
        run_kind="core-planning",
        semantic_layer="normalized",
        engine_version=worker_main.CORE_ENGINE_DESCRIPTOR,
        input_fingerprint="0" * 64,
        payload={},
    )
    queue = FakeQueue(run)
    monkeypatch.setattr(worker_main, "load_planning_input", lambda organization_id, scenario_revision_id: planning_input)

    processed = worker_main.process_one(queue, "planning-worker")

    assert processed is True
    assert queue.succeeded is None
    assert queue.failed == "queued input fingerprint does not match immutable scenario snapshot"
    assert queue.retryable is False
