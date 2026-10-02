"""OferBus persistence foundation.

Revision ID: 0001_foundation
Revises: None
Create Date: 2026-10-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_foundation"
down_revision: Union[str, Sequence[str], None] = None
branch_labels = None
depends_on = None

SCHEMA = "oferbus"


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS oferbus")

    op.create_table(
        "organization",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("organization_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        schema=SCHEMA,
    )

    op.create_table(
        "app_user",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("display_name", sa.String(240), nullable=False),
        sa.Column("email", sa.String(320)),
        sa.Column("external_subject", sa.String(320), unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema=SCHEMA,
    )

    op.create_table(
        "organization_membership",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_key", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["oferbus.organization.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["oferbus.app_user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("organization_id", "user_id"),
        schema=SCHEMA,
    )

    op.create_table(
        "municipality",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("state_region", sa.String(120)),
        sa.Column("country_code", sa.String(2), nullable=False, server_default="BR"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["oferbus.organization.id"]),
        sa.UniqueConstraint("organization_id", "id", name="uq_municipality_org_id"),
        schema=SCHEMA,
    )

    op.create_table(
        "transit_operator",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("municipality_id", postgresql.UUID(as_uuid=True)),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["oferbus.organization.id"]),
        sa.ForeignKeyConstraint(["organization_id", "municipality_id"], ["oferbus.municipality.organization_id", "oferbus.municipality.id"], name="fk_transit_operator_tenant_municipality"),
        sa.UniqueConstraint("organization_id", "id", name="uq_transit_operator_org_id"),
        schema=SCHEMA,
    )

    op.create_table(
        "terminal",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("municipality_id", postgresql.UUID(as_uuid=True)),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("allows_storage", sa.Boolean()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["oferbus.organization.id"]),
        sa.ForeignKeyConstraint(["organization_id", "municipality_id"], ["oferbus.municipality.organization_id", "oferbus.municipality.id"], name="fk_terminal_tenant_municipality"),
        sa.UniqueConstraint("organization_id", "id", name="uq_terminal_org_id"),
        schema=SCHEMA,
    )

    op.create_table(
        "transit_line",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("municipality_id", postgresql.UUID(as_uuid=True)),
        sa.Column("operator_id", postgresql.UUID(as_uuid=True)),
        sa.Column("public_code", sa.String(80)),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("legacy_operation_type_code", sa.Integer()),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["organization_id"], ["oferbus.organization.id"]),
        sa.ForeignKeyConstraint(["organization_id", "municipality_id"], ["oferbus.municipality.organization_id", "oferbus.municipality.id"], name="fk_transit_line_tenant_municipality"),
        sa.ForeignKeyConstraint(["organization_id", "operator_id"], ["oferbus.transit_operator.organization_id", "oferbus.transit_operator.id"], name="fk_transit_line_tenant_operator"),
        sa.UniqueConstraint("organization_id", "id", name="uq_transit_line_org_id"),
        schema=SCHEMA,
    )

    op.create_table(
        "line_direction",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("line_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("direction_key", sa.String(64), nullable=False),
        sa.Column("origin_terminal_id", postgresql.UUID(as_uuid=True)),
        sa.Column("destination_terminal_id", postgresql.UUID(as_uuid=True)),
        sa.Column("extension_km", sa.Numeric(12, 3)),
        sa.Column("legacy_direction_number", sa.Integer()),
        sa.ForeignKeyConstraint(["organization_id"], ["oferbus.organization.id"]),
        sa.ForeignKeyConstraint(["organization_id", "line_id"], ["oferbus.transit_line.organization_id", "oferbus.transit_line.id"], name="fk_line_direction_tenant_line"),
        sa.ForeignKeyConstraint(["organization_id", "origin_terminal_id"], ["oferbus.terminal.organization_id", "oferbus.terminal.id"], name="fk_line_direction_tenant_origin_terminal"),
        sa.ForeignKeyConstraint(["organization_id", "destination_terminal_id"], ["oferbus.terminal.organization_id", "oferbus.terminal.id"], name="fk_line_direction_tenant_destination_terminal"),
        sa.CheckConstraint("extension_km IS NULL OR extension_km >= 0", name="ck_line_direction_extension_nonnegative"),
        sa.UniqueConstraint("organization_id", "id", name="uq_line_direction_org_id"),
        sa.UniqueConstraint("line_id", "direction_key", name="uq_line_direction_line_key"),
        schema=SCHEMA,
    )

    op.create_table(
        "planning_project",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["organization_id"], ["oferbus.organization.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["oferbus.app_user.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("organization_id", "id", name="uq_planning_project_org_id"),
        schema=SCHEMA,
    )

    op.create_table(
        "project_line",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("line_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["oferbus.organization.id"]),
        sa.ForeignKeyConstraint(["organization_id", "project_id"], ["oferbus.planning_project.organization_id", "oferbus.planning_project.id"], name="fk_project_line_tenant_project"),
        sa.ForeignKeyConstraint(["organization_id", "line_id"], ["oferbus.transit_line.organization_id", "oferbus.transit_line.id"], name="fk_project_line_tenant_line"),
        sa.PrimaryKeyConstraint("project_id", "line_id"),
        schema=SCHEMA,
    )

    op.create_table(
        "scenario",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["organization_id"], ["oferbus.organization.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["oferbus.app_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id", "project_id"], ["oferbus.planning_project.organization_id", "oferbus.planning_project.id"], name="fk_scenario_tenant_project"),
        sa.UniqueConstraint("organization_id", "id", name="uq_scenario_org_id"),
        schema=SCHEMA,
    )

    op.create_table(
        "scenario_revision",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column("parent_revision_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reason", sa.Text()),
        sa.Column("input_fingerprint", sa.String(128)),
        sa.ForeignKeyConstraint(["organization_id"], ["oferbus.organization.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["oferbus.app_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id", "scenario_id"], ["oferbus.scenario.organization_id", "oferbus.scenario.id"], name="fk_scenario_revision_tenant_scenario"),
        sa.ForeignKeyConstraint(["organization_id", "parent_revision_id"], ["oferbus.scenario_revision.organization_id", "oferbus.scenario_revision.id"], name="fk_scenario_revision_tenant_parent"),
        sa.CheckConstraint("revision_no > 0", name="ck_scenario_revision_revision_positive"),
        sa.UniqueConstraint("organization_id", "id", name="uq_scenario_revision_org_id"),
        sa.UniqueConstraint("scenario_id", "revision_no", name="uq_scenario_revision_number"),
        schema=SCHEMA,
    )

    op.create_table(
        "computation_run",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scenario_revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_kind", sa.String(80), nullable=False),
        sa.Column("semantic_layer", sa.String(32), nullable=False),
        sa.Column("engine_version", sa.String(80), nullable=False),
        sa.Column("engine_source_revision", sa.String(80)),
        sa.Column("deterministic_seed", sa.BigInteger()),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("input_fingerprint", sa.String(128)),
        sa.Column("output_fingerprint", sa.String(128)),
        sa.Column("diagnostics", postgresql.JSONB()),
        sa.ForeignKeyConstraint(["organization_id"], ["oferbus.organization.id"]),
        sa.ForeignKeyConstraint(["organization_id", "scenario_revision_id"], ["oferbus.scenario_revision.organization_id", "oferbus.scenario_revision.id"], name="fk_computation_run_tenant_scenario_revision"),
        sa.CheckConstraint("semantic_layer IN ('legacy-exact','normalized','modern')", name="ck_computation_run_semantic_layer_valid"),
        sa.UniqueConstraint("organization_id", "id", name="uq_computation_run_org_id"),
        schema=SCHEMA,
    )

    op.create_index("ix_scenario_revision_scenario", "scenario_revision", ["scenario_id", "revision_no"], schema=SCHEMA)
    op.create_index("ix_computation_run_scenario_status", "computation_run", ["scenario_revision_id", "status"], schema=SCHEMA)


def downgrade() -> None:
    for table in [
        "computation_run", "scenario_revision", "scenario", "project_line",
        "planning_project", "line_direction", "transit_line", "terminal",
        "transit_operator", "municipality", "organization_membership",
        "app_user", "organization",
    ]:
        op.drop_table(table, schema=SCHEMA)
    op.execute("DROP SCHEMA IF EXISTS oferbus")
