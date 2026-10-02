from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ComputationJob(Base):
    """Durable asynchronous execution metadata for a ComputationRun."""

    __tablename__ = "computation_job"

    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("oferbus.organization.id", ondelete="RESTRICT"),
        nullable=False,
    )
    submitted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("oferbus.app_user.id", ondelete="SET NULL"),
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(160))
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lease_owner: Mapped[str | None] = mapped_column(String(160))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    last_error: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("organization_id", "run_id", name="uq_computation_job_org_run"),
        ForeignKeyConstraint(
            ["organization_id", "run_id"],
            ["oferbus.computation_run.organization_id", "oferbus.computation_run.id"],
            name="fk_computation_job_tenant_run",
            ondelete="CASCADE",
        ),
        CheckConstraint("progress_percent BETWEEN 0 AND 100", name="progress"),
        CheckConstraint("attempt_count >= 0", name="attempt_count"),
        CheckConstraint("max_attempts >= 1", name="max_attempts"),
        Index("ix_computation_job_claim", "available_at", "queued_at"),
        Index(
            "uq_computation_job_org_idempotency",
            "organization_id",
            "idempotency_key",
            unique=True,
            postgresql_where=text("idempotency_key IS NOT NULL"),
        ),
    )
