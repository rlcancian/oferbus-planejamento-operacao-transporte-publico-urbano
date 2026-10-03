"""Asynchronous computation queue foundation.

Revision ID: 0003_async_computation
Revises: 0002_identity_tenancy
Create Date: 2026-10-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_async_computation"
down_revision: Union[str, Sequence[str], None] = "0002_identity_tenancy"
branch_labels = None
depends_on = None

SCHEMA = "oferbus"


def upgrade() -> None:
    op.create_check_constraint(
        "ck_computation_run_status_valid",
        "computation_run",
        "status IN ('queued','retry_wait','running','succeeded','failed','cancelled')",
        schema=SCHEMA,
    )
    op.create_index(
        "ix_computation_run_org_status",
        "computation_run",
        ["organization_id", "status"],
        schema=SCHEMA,
    )

    op.create_table(
        "computation_job",
        sa.Column("run_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("submitted_by", postgresql.UUID(as_uuid=True)),
        sa.Column("idempotency_key", sa.String(160)),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("claimed_at", sa.DateTime(timezone=True)),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True)),
        sa.Column("lease_owner", sa.String(160)),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True)),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("last_error", sa.Text()),
        sa.ForeignKeyConstraint(["organization_id"], ["oferbus.organization.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["submitted_by"], ["oferbus.app_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["organization_id", "run_id"],
            ["oferbus.computation_run.organization_id", "oferbus.computation_run.id"],
            name="fk_computation_job_tenant_run",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("organization_id", "run_id", name="uq_computation_job_org_run"),
        sa.CheckConstraint("progress_percent BETWEEN 0 AND 100", name="ck_computation_job_progress"),
        sa.CheckConstraint("attempt_count >= 0", name="ck_computation_job_attempt_count"),
        sa.CheckConstraint("max_attempts >= 1", name="ck_computation_job_max_attempts"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_computation_job_claim",
        "computation_job",
        ["available_at", "queued_at"],
        schema=SCHEMA,
    )
    op.create_index(
        "uq_computation_job_org_idempotency",
        "computation_job",
        ["organization_id", "idempotency_key"],
        unique=True,
        schema=SCHEMA,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_computation_job_org_idempotency", table_name="computation_job", schema=SCHEMA)
    op.drop_index("ix_computation_job_claim", table_name="computation_job", schema=SCHEMA)
    op.drop_table("computation_job", schema=SCHEMA)
    op.drop_index("ix_computation_run_org_status", table_name="computation_run", schema=SCHEMA)
    op.drop_constraint("ck_computation_run_status_valid", "computation_run", type_="check", schema=SCHEMA)
