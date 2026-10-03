"""Phase B planning input persistence.

Revision ID: 0004_planning_inputs
Revises: 0003_async_computation
Create Date: 2026-10-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0004_planning_inputs"
down_revision: Union[str, Sequence[str], None] = "0003_async_computation"
branch_labels = None
depends_on = None

SCHEMA = "oferbus"


def upgrade() -> None:
    op.create_table(
        "observed_trip_dataset",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("line_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["oferbus.organization.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["oferbus.app_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["organization_id", "line_id"],
            ["oferbus.transit_line.organization_id", "oferbus.transit_line.id"],
            name="fk_observed_trip_dataset_tenant_line",
        ),
        sa.UniqueConstraint("organization_id", "id", name="uq_observed_trip_dataset_org_id"),
        schema=SCHEMA,
    )

    op.create_table(
        "observed_trip_dataset_revision",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column("parent_revision_id", postgresql.UUID(as_uuid=True)),
        sa.Column("source_label", sa.String(240)),
        sa.Column("source_metadata", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("content_fingerprint", sa.String(64), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["oferbus.organization.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["oferbus.app_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["organization_id", "dataset_id"],
            ["oferbus.observed_trip_dataset.organization_id", "oferbus.observed_trip_dataset.id"],
            name="fk_observed_trip_dataset_revision_tenant_dataset",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "parent_revision_id"],
            ["oferbus.observed_trip_dataset_revision.organization_id", "oferbus.observed_trip_dataset_revision.id"],
            name="fk_observed_trip_dataset_revision_tenant_parent",
        ),
        sa.UniqueConstraint("organization_id", "id", name="uq_observed_trip_dataset_revision_org_id"),
        sa.UniqueConstraint("dataset_id", "revision_no", name="uq_observed_trip_dataset_revision_number"),
        sa.CheckConstraint("revision_no > 0", name="ck_observed_trip_dataset_revision_observed_revision_positive"),
        schema=SCHEMA,
    )

    op.create_table(
        "observed_trip_observation",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dataset_revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("direction_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.Column("departure_service_minute", sa.Integer(), nullable=False),
        sa.Column("passengers", sa.Integer(), nullable=False),
        sa.Column("critical_passengers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("travel_time_min", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["organization_id"], ["oferbus.organization.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["organization_id", "dataset_revision_id"],
            ["oferbus.observed_trip_dataset_revision.organization_id", "oferbus.observed_trip_dataset_revision.id"],
            name="fk_observed_trip_observation_tenant_revision",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "direction_id"],
            ["oferbus.line_direction.organization_id", "oferbus.line_direction.id"],
            name="fk_observed_trip_observation_tenant_direction",
        ),
        sa.UniqueConstraint(
            "dataset_revision_id", "direction_id", "sequence_no",
            name="uq_observed_trip_observation_sequence",
        ),
        sa.CheckConstraint("sequence_no > 0", name="ck_observed_trip_observation_observed_sequence_positive"),
        sa.CheckConstraint("departure_service_minute >= 0", name="ck_observed_trip_observation_observed_departure_nonnegative"),
        sa.CheckConstraint("passengers >= 0", name="ck_observed_trip_observation_observed_passengers_nonnegative"),
        sa.CheckConstraint("critical_passengers >= 0", name="ck_observed_trip_observation_observed_critical_passengers_nonnegative"),
        sa.CheckConstraint("travel_time_min >= 0", name="ck_observed_trip_observation_observed_travel_time_nonnegative"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_observed_trip_observation_revision_direction",
        "observed_trip_observation",
        ["dataset_revision_id", "direction_id", "sequence_no"],
        schema=SCHEMA,
    )

    op.create_table(
        "scenario_planning_input",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scenario_revision_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("semantic_layer", sa.String(32), nullable=False),
        sa.Column("vehicle_seats", sa.Integer(), nullable=False),
        sa.Column("vehicle_free_area_m2", sa.Numeric(12, 4), nullable=False),
        sa.Column("vehicle_capacity_level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("cost_mode", sa.String(32), nullable=False, server_default="per_km"),
        sa.Column("cost_per_km", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("fixed_cost_per_vehicle", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("variable_cost_per_km", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("max_headway_min", sa.Integer(), nullable=False),
        sa.Column("project_capacity_passengers", sa.Numeric(12, 4), nullable=False),
        sa.Column("valley_capacity_passengers", sa.Numeric(12, 4), nullable=False),
        sa.Column("boarding_seconds_per_passenger", sa.Numeric(12, 4), nullable=False),
        sa.Column("alighting_seconds_per_passenger", sa.Numeric(12, 4), nullable=False),
        sa.Column("radial", sa.Boolean(), nullable=False),
        sa.Column("create_express_returns", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("mean_renewal_index", sa.Numeric(12, 6), nullable=False, server_default="1"),
        sa.Column("typical_day_participation", sa.Numeric(12, 6), nullable=False, server_default="1"),
        sa.Column("equivalent_passenger_index", sa.Numeric(12, 6), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["oferbus.organization.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["organization_id", "scenario_revision_id"],
            ["oferbus.scenario_revision.organization_id", "oferbus.scenario_revision.id"],
            name="fk_scenario_planning_input_tenant_revision",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("organization_id", "scenario_revision_id", name="uq_scenario_planning_input_org_revision"),
        sa.CheckConstraint("semantic_layer IN ('legacy-exact','normalized','modern')", name="ck_scenario_planning_input_scenario_planning_semantic_layer_valid"),
        sa.CheckConstraint("vehicle_seats >= 0", name="ck_scenario_planning_input_scenario_planning_vehicle_seats_nonnegative"),
        sa.CheckConstraint("vehicle_free_area_m2 > 0", name="ck_scenario_planning_input_scenario_planning_vehicle_area_positive"),
        sa.CheckConstraint("vehicle_capacity_level >= 0", name="ck_scenario_planning_input_scenario_planning_capacity_level_nonnegative"),
        sa.CheckConstraint("cost_mode IN ('per_km','fixed_variable')", name="ck_scenario_planning_input_scenario_planning_cost_mode_valid"),
        sa.CheckConstraint("max_headway_min > 0", name="ck_scenario_planning_input_scenario_planning_headway_positive"),
        sa.CheckConstraint("project_capacity_passengers > 0", name="ck_scenario_planning_input_scenario_planning_capacity_positive"),
        sa.CheckConstraint("valley_capacity_passengers > 0", name="ck_scenario_planning_input_scenario_planning_valley_capacity_positive"),
        sa.CheckConstraint("mean_renewal_index > 0", name="ck_scenario_planning_input_scenario_planning_mean_ir_positive"),
        sa.CheckConstraint("equivalent_passenger_index > 0", name="ck_scenario_planning_input_scenario_planning_equivalent_index_positive"),
        schema=SCHEMA,
    )

    op.create_table(
        "scenario_direction_planning_input",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scenario_revision_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("direction_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dataset_revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("direction_key", sa.String(64), nullable=False),
        sa.Column("legacy_direction_number", sa.Integer(), nullable=False),
        sa.Column("service_start_minute", sa.Integer(), nullable=False),
        sa.Column("service_end_minute", sa.Integer(), nullable=False),
        sa.Column("demand_passengers_per_minute", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("renewal_index_curve", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("travel_time_min_curve", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("demand_maximum_passengers_per_minute", sa.Numeric(14, 8), nullable=False),
        sa.Column("extension_km", sa.Numeric(12, 3), nullable=False),
        sa.Column("storage_at_departure_terminal", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["oferbus.organization.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["organization_id", "scenario_revision_id"],
            ["oferbus.scenario_revision.organization_id", "oferbus.scenario_revision.id"],
            name="fk_scenario_direction_planning_tenant_revision",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "direction_id"],
            ["oferbus.line_direction.organization_id", "oferbus.line_direction.id"],
            name="fk_scenario_direction_planning_tenant_direction",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "dataset_revision_id"],
            ["oferbus.observed_trip_dataset_revision.organization_id", "oferbus.observed_trip_dataset_revision.id"],
            name="fk_scenario_direction_planning_tenant_dataset_revision",
        ),
        sa.UniqueConstraint(
            "scenario_revision_id", "legacy_direction_number",
            name="uq_scenario_direction_planning_legacy_number",
        ),
        sa.CheckConstraint("legacy_direction_number > 0", name="ck_scenario_direction_planning_input_scenario_direction_legacy_number_positive"),
        sa.CheckConstraint("service_start_minute >= 0", name="ck_scenario_direction_planning_input_scenario_direction_start_nonnegative"),
        sa.CheckConstraint("service_end_minute >= service_start_minute", name="ck_scenario_direction_planning_input_scenario_direction_window_valid"),
        sa.CheckConstraint("demand_maximum_passengers_per_minute >= 0", name="ck_scenario_direction_planning_input_scenario_direction_demand_max_nonnegative"),
        sa.CheckConstraint("extension_km > 0", name="ck_scenario_direction_planning_input_scenario_direction_extension_positive"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_scenario_direction_planning_revision",
        "scenario_direction_planning_input",
        ["scenario_revision_id", "legacy_direction_number"],
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_index("ix_scenario_direction_planning_revision", table_name="scenario_direction_planning_input", schema=SCHEMA)
    op.drop_table("scenario_direction_planning_input", schema=SCHEMA)
    op.drop_table("scenario_planning_input", schema=SCHEMA)
    op.drop_index("ix_observed_trip_observation_revision_direction", table_name="observed_trip_observation", schema=SCHEMA)
    op.drop_table("observed_trip_observation", schema=SCHEMA)
    op.drop_table("observed_trip_dataset_revision", schema=SCHEMA)
    op.drop_table("observed_trip_dataset", schema=SCHEMA)
