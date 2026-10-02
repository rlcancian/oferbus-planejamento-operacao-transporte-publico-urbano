import uuid
from types import SimpleNamespace

import pytest

from oferbus_jobs import IdempotencyConflictError, RunSubmission
from oferbus_jobs.queue import _assert_idempotent_compatible


def _submission(**overrides) -> RunSubmission:
    values = dict(
        organization_id=uuid.uuid4(),
        scenario_revision_id=uuid.uuid4(),
        submitted_by=uuid.uuid4(),
        run_kind="core-planning",
        semantic_layer="normalized",
        engine_version="reference-bridge:0.1.0",
        input_fingerprint="a" * 64,
        idempotency_key="same-key",
        payload={},
    )
    values.update(overrides)
    return RunSubmission(**values)


def _existing(submission: RunSubmission):
    run = SimpleNamespace(
        scenario_revision_id=submission.scenario_revision_id,
        run_kind=submission.run_kind,
        semantic_layer=submission.semantic_layer,
        engine_version=submission.engine_version,
        engine_source_revision=submission.engine_source_revision,
        deterministic_seed=submission.deterministic_seed,
        input_fingerprint=submission.input_fingerprint,
    )
    job = SimpleNamespace(payload=submission.payload or {})
    return run, job


def test_same_idempotency_key_accepts_identical_computation_identity() -> None:
    submission = _submission()
    run, job = _existing(submission)

    _assert_idempotent_compatible(run, job, submission)


def test_same_idempotency_key_rejects_different_scenario_revision() -> None:
    submission = _submission()
    run, job = _existing(submission)
    conflicting = _submission(
        organization_id=submission.organization_id,
        idempotency_key=submission.idempotency_key,
        scenario_revision_id=uuid.uuid4(),
    )

    with pytest.raises(IdempotencyConflictError) as exc_info:
        _assert_idempotent_compatible(run, job, conflicting)

    assert "scenario_revision_id" in str(exc_info.value)


def test_same_idempotency_key_rejects_different_input_fingerprint() -> None:
    submission = _submission()
    run, job = _existing(submission)
    conflicting = _submission(
        organization_id=submission.organization_id,
        idempotency_key=submission.idempotency_key,
        scenario_revision_id=submission.scenario_revision_id,
        input_fingerprint="b" * 64,
    )

    with pytest.raises(IdempotencyConflictError) as exc_info:
        _assert_idempotent_compatible(run, job, conflicting)

    assert "input_fingerprint" in str(exc_info.value)
