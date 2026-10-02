from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from sqlalchemy import and_, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from oferbus_db import ComputationJob, ComputationRun, get_session_factory

TERMINAL_STATUSES = frozenset({"succeeded", "failed", "cancelled"})
CLAIMABLE_STATUSES = frozenset({"queued", "retry_wait"})


@dataclass(frozen=True)
class RunSubmission:
    organization_id: uuid.UUID
    scenario_revision_id: uuid.UUID
    submitted_by: uuid.UUID | None
    run_kind: str
    semantic_layer: str
    engine_version: str
    engine_source_revision: str | None = None
    deterministic_seed: int | None = None
    idempotency_key: str | None = None
    payload: dict[str, Any] | None = None
    max_attempts: int = 3


@dataclass(frozen=True)
class RunSnapshot:
    run_id: uuid.UUID
    organization_id: uuid.UUID
    run_kind: str
    semantic_layer: str
    status: str
    progress_percent: int
    attempt_count: int
    max_attempts: int
    queued_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    last_error: str | None
    diagnostics: dict[str, Any] | None


class JobQueue(Protocol):
    def submit(self, submission: RunSubmission) -> RunSnapshot: ...
    def get(self, organization_id: uuid.UUID, run_id: uuid.UUID) -> RunSnapshot | None: ...
    def claim(self, worker_id: str, lease_seconds: int = 60) -> RunSnapshot | None: ...
    def heartbeat(self, run_id: uuid.UUID, worker_id: str, progress_percent: int | None = None, lease_seconds: int = 60) -> None: ...
    def succeed(self, run_id: uuid.UUID, worker_id: str, diagnostics: dict[str, Any] | None = None) -> None: ...
    def fail(self, run_id: uuid.UUID, worker_id: str, error: str, retryable: bool = True) -> None: ...


def retry_delay_seconds(attempt_count: int) -> int:
    return min(300, max(5, 5 * (2 ** max(0, attempt_count - 1))))


def _snapshot(run: ComputationRun, job: ComputationJob) -> RunSnapshot:
    return RunSnapshot(
        run_id=run.id,
        organization_id=run.organization_id,
        run_kind=run.run_kind,
        semantic_layer=run.semantic_layer,
        status=run.status,
        progress_percent=job.progress_percent,
        attempt_count=job.attempt_count,
        max_attempts=job.max_attempts,
        queued_at=job.queued_at,
        started_at=run.started_at,
        completed_at=run.completed_at,
        last_error=job.last_error,
        diagnostics=run.diagnostics,
    )


class PostgresComputationQueue:
    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        self._session_factory = session_factory or get_session_factory()

    def submit(self, submission: RunSubmission) -> RunSnapshot:
        if submission.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        now = datetime.now(UTC)
        with self._session_factory() as session:
            if submission.idempotency_key:
                existing = session.execute(
                    select(ComputationRun, ComputationJob)
                    .join(ComputationJob, ComputationJob.run_id == ComputationRun.id)
                    .where(
                        ComputationJob.organization_id == submission.organization_id,
                        ComputationJob.idempotency_key == submission.idempotency_key,
                    )
                ).one_or_none()
                if existing is not None:
                    return _snapshot(*existing)

            run = ComputationRun(
                organization_id=submission.organization_id,
                scenario_revision_id=submission.scenario_revision_id,
                run_kind=submission.run_kind,
                semantic_layer=submission.semantic_layer,
                engine_version=submission.engine_version,
                engine_source_revision=submission.engine_source_revision,
                deterministic_seed=submission.deterministic_seed,
                status="queued",
            )
            session.add(run)
            session.flush()

            job = ComputationJob(
                run_id=run.id,
                organization_id=submission.organization_id,
                submitted_by=submission.submitted_by,
                idempotency_key=submission.idempotency_key,
                payload=submission.payload or {},
                progress_percent=0,
                queued_at=now,
                available_at=now,
                attempt_count=0,
                max_attempts=submission.max_attempts,
            )
            session.add(job)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                if not submission.idempotency_key:
                    raise
                existing = session.execute(
                    select(ComputationRun, ComputationJob)
                    .join(ComputationJob, ComputationJob.run_id == ComputationRun.id)
                    .where(
                        ComputationJob.organization_id == submission.organization_id,
                        ComputationJob.idempotency_key == submission.idempotency_key,
                    )
                ).one()
                return _snapshot(*existing)

            return _snapshot(run, job)

    def get(self, organization_id: uuid.UUID, run_id: uuid.UUID) -> RunSnapshot | None:
        with self._session_factory() as session:
            row = session.execute(
                select(ComputationRun, ComputationJob)
                .join(ComputationJob, ComputationJob.run_id == ComputationRun.id)
                .where(
                    ComputationRun.organization_id == organization_id,
                    ComputationRun.id == run_id,
                )
            ).one_or_none()
            return _snapshot(*row) if row is not None else None

    def claim(self, worker_id: str, lease_seconds: int = 60) -> RunSnapshot | None:
        now = datetime.now(UTC)
        self._fail_exhausted_expired(now)

        with self._session_factory() as session:
            claimable = or_(
                and_(
                    ComputationRun.status.in_(CLAIMABLE_STATUSES),
                    ComputationJob.available_at <= now,
                    ComputationJob.attempt_count < ComputationJob.max_attempts,
                ),
                and_(
                    ComputationRun.status == "running",
                    ComputationJob.lease_expires_at < now,
                    ComputationJob.attempt_count < ComputationJob.max_attempts,
                ),
            )
            row = session.execute(
                select(ComputationRun, ComputationJob)
                .join(ComputationJob, ComputationJob.run_id == ComputationRun.id)
                .where(claimable)
                .order_by(ComputationJob.available_at, ComputationJob.queued_at, ComputationRun.id)
                .with_for_update(skip_locked=True)
                .limit(1)
            ).one_or_none()
            if row is None:
                return None

            run, job = row
            run.status = "running"
            run.started_at = run.started_at or now
            job.attempt_count += 1
            job.claimed_at = now
            job.heartbeat_at = now
            job.lease_owner = worker_id
            job.lease_expires_at = now + timedelta(seconds=lease_seconds)
            job.last_error = None
            session.commit()
            return _snapshot(run, job)

    def heartbeat(
        self,
        run_id: uuid.UUID,
        worker_id: str,
        progress_percent: int | None = None,
        lease_seconds: int = 60,
    ) -> None:
        if progress_percent is not None and not 0 <= progress_percent <= 100:
            raise ValueError("progress_percent must be between 0 and 100")

        now = datetime.now(UTC)
        values: dict[str, Any] = {
            "heartbeat_at": now,
            "lease_expires_at": now + timedelta(seconds=lease_seconds),
        }
        if progress_percent is not None:
            values["progress_percent"] = progress_percent

        with self._session_factory() as session:
            result = session.execute(
                update(ComputationJob)
                .where(
                    ComputationJob.run_id == run_id,
                    ComputationJob.lease_owner == worker_id,
                )
                .values(**values)
            )
            if result.rowcount != 1:
                session.rollback()
                raise RuntimeError("worker does not own the active lease")
            session.commit()

    def succeed(
        self,
        run_id: uuid.UUID,
        worker_id: str,
        diagnostics: dict[str, Any] | None = None,
    ) -> None:
        now = datetime.now(UTC)
        with self._session_factory() as session:
            row = session.execute(
                select(ComputationRun, ComputationJob)
                .join(ComputationJob, ComputationJob.run_id == ComputationRun.id)
                .where(
                    ComputationRun.id == run_id,
                    ComputationRun.status == "running",
                    ComputationJob.lease_owner == worker_id,
                )
                .with_for_update()
            ).one_or_none()
            if row is None:
                raise RuntimeError("worker does not own the active lease")

            run, job = row
            run.status = "succeeded"
            run.completed_at = now
            run.diagnostics = diagnostics or {}
            job.progress_percent = 100
            job.heartbeat_at = now
            job.lease_owner = None
            job.lease_expires_at = None
            session.commit()

    def fail(
        self,
        run_id: uuid.UUID,
        worker_id: str,
        error: str,
        retryable: bool = True,
    ) -> None:
        now = datetime.now(UTC)
        with self._session_factory() as session:
            row = session.execute(
                select(ComputationRun, ComputationJob)
                .join(ComputationJob, ComputationJob.run_id == ComputationRun.id)
                .where(
                    ComputationRun.id == run_id,
                    ComputationRun.status == "running",
                    ComputationJob.lease_owner == worker_id,
                )
                .with_for_update()
            ).one_or_none()
            if row is None:
                raise RuntimeError("worker does not own the active lease")

            run, job = row
            can_retry = retryable and job.attempt_count < job.max_attempts
            job.last_error = error[:4000]
            job.heartbeat_at = now
            job.lease_owner = None
            job.lease_expires_at = None
            if can_retry:
                run.status = "retry_wait"
                job.available_at = now + timedelta(seconds=retry_delay_seconds(job.attempt_count))
            else:
                run.status = "failed"
                run.completed_at = now
            session.commit()

    def _fail_exhausted_expired(self, now: datetime) -> None:
        with self._session_factory() as session:
            rows = session.execute(
                select(ComputationRun, ComputationJob)
                .join(ComputationJob, ComputationJob.run_id == ComputationRun.id)
                .where(
                    ComputationRun.status == "running",
                    ComputationJob.lease_expires_at < now,
                    ComputationJob.attempt_count >= ComputationJob.max_attempts,
                )
                .with_for_update(skip_locked=True)
            ).all()
            for run, job in rows:
                run.status = "failed"
                run.completed_at = now
                job.lease_owner = None
                job.lease_expires_at = None
                job.last_error = "worker lease expired after maximum attempts"
            session.commit()
