"""Phase C.2 versioned plan editing boundary.

Revision ID: 0006_plan_editing
Revises: 0005_planning_results
Create Date: 2026-10-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0006_plan_editing"
down_revision: Union[str, Sequence[str], None] = "0005_planning_results"
branch_labels = None
depends_on = None

SCHEMA = "oferbus"


def upgrade() -> None:
    op.add_column("plan_revision", sa.Column("created_by", postgresql.UUID(as_uuid=True)), schema=SCHEMA)
    op.add_column("plan_revision", sa.Column("change_reason", sa.Text()), schema=SCHEMA)
    op.create_foreign_key(
        "fk_plan_revision_created_by",
        "plan_revision", "app_user",
        ["created_by"], ["id"],
        source_schema=SCHEMA, referent_schema=SCHEMA,
        ondelete="SET NULL",
    )

    op.create_table(
        "plan_edit_command",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_command_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_plan_revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("derived_plan_revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("command_type", sa.String(64), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("command_type IN ('fork')", name="ck_plan_edit_command_type_valid"),
        sa.ForeignKeyConstraint(["organization_id"], ["oferbus.organization.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["organization_id", "parent_plan_revision_id"],
            ["oferbus.plan_revision.organization_id", "oferbus.plan_revision.id"],
            name="fk_plan_edit_command_tenant_parent",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "derived_plan_revision_id"],
            ["oferbus.plan_revision.organization_id", "oferbus.plan_revision.id"],
            name="fk_plan_edit_command_tenant_derived",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["oferbus.app_user.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("organization_id", "id", name="uq_plan_edit_command_org_id"),
        sa.UniqueConstraint("organization_id", "client_command_id", name="uq_plan_edit_command_client_id"),
        sa.UniqueConstraint("derived_plan_revision_id", name="uq_plan_edit_command_derived_revision"),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("plan_edit_command", schema=SCHEMA)
    op.drop_constraint("fk_plan_revision_created_by", "plan_revision", schema=SCHEMA, type_="foreignkey")
    op.drop_column("plan_revision", "change_reason", schema=SCHEMA)
    op.drop_column("plan_revision", "created_by", schema=SCHEMA)
