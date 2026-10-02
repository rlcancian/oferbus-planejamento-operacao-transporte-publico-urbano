"""Identity, tenancy and audit foundation.

Revision ID: 0002_identity_tenancy
Revises: 0001_foundation
Create Date: 2026-10-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_identity_tenancy"
down_revision: Union[str, Sequence[str], None] = "0001_foundation"
branch_labels = None
depends_on = None

SCHEMA = "oferbus"


def upgrade() -> None:
    op.create_check_constraint(
        "ck_membership_role_valid",
        "organization_membership",
        "role_key IN ('owner','admin','planner','viewer')",
        schema=SCHEMA,
    )
    op.create_check_constraint(
        "ck_membership_status_valid",
        "organization_membership",
        "status IN ('active','invited','suspended')",
        schema=SCHEMA,
    )

    op.create_table(
        "audit_event",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("actor_subject", sa.String(320)),
        sa.Column("actor_role_key", sa.String(64)),
        sa.Column("event_type", sa.String(120), nullable=False),
        sa.Column("entity_type", sa.String(120), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True)),
        sa.Column("correlation_id", sa.String(120)),
        sa.Column("event_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["organization_id"], ["oferbus.organization.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["oferbus.app_user.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("organization_id", "id", name="uq_audit_event_org_id"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_audit_event_org_time",
        "audit_event",
        ["organization_id", "event_at"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_audit_event_actor",
        "audit_event",
        ["actor_user_id", "event_at"],
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_index("ix_audit_event_actor", table_name="audit_event", schema=SCHEMA)
    op.drop_index("ix_audit_event_org_time", table_name="audit_event", schema=SCHEMA)
    op.drop_table("audit_event", schema=SCHEMA)
    op.drop_constraint("ck_membership_status_valid", "organization_membership", type_="check", schema=SCHEMA)
    op.drop_constraint("ck_membership_role_valid", "organization_membership", type_="check", schema=SCHEMA)
