"""Phase B planning result persistence.

Revision ID: 0005_planning_results
Revises: 0004_planning_inputs
Create Date: 2026-10-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005_planning_results"
down_revision: Union[str, Sequence[str], None] = "0004_planning_inputs"
branch_labels = None
depends_on = None

SCHEMA = "oferbus"


def upgrade() -> None:
    op.create_table(
        "plan_revision",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scenario_revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("computation_run_id", postgresql.UUID(as_uuid=True)),
        sa.Column("parent_plan_revision_id", postgresql.UUID(as_uuid=True)),
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column("source_kind", sa.String(32), nullable=False, server_default="computed"),
        sa.Column("semantic_layer", sa.String(32), nullable=False),
        sa.Column("engine_version", sa.String(80), nullable=False),
        sa.Column("input_fingerprint", sa.String(128), nullable=False),
        sa.Column("output_fingerprint", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("revision_no > 0", name="ck_plan_revision_revision_positive"),
        sa.CheckConstraint("source_kind IN ('computed','manual')", name="ck_plan_revision_source_kind_valid"),
        sa.CheckConstraint(
            "semantic_layer IN ('legacy-exact','normalized','modern')",
            name="ck_plan_revision_semantic_layer_valid",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["oferbus.organization.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["organization_id", "scenario_revision_id"],
            ["oferbus.scenario_revision.organization_id", "oferbus.scenario_revision.id"],
            name="fk_plan_revision_tenant_scenario_revision",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "computation_run_id"],
            ["oferbus.computation_run.organization_id", "oferbus.computation_run.id"],
            name="fk_plan_revision_tenant_computation_run",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "parent_plan_revision_id"],
            ["oferbus.plan_revision.organization_id", "oferbus.plan_revision.id"],
            name="fk_plan_revision_tenant_parent",
        ),
        sa.UniqueConstraint("organization_id", "id", name="uq_plan_revision_org_id"),
        sa.UniqueConstraint("scenario_revision_id", "revision_no", name="uq_plan_revision_scenario_revision_no"),
        sa.UniqueConstraint("computation_run_id", name="uq_plan_revision_computation_run"),
        schema=SCHEMA,
    )

    op.create_table(
        "planned_trip",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.Column("direction_key", sa.String(64), nullable=False),
        sa.Column("legacy_direction_number", sa.Integer(), nullable=False),
        sa.Column("departure_service_minute", sa.Integer(), nullable=False),
        sa.Column("arrival_service_minute", sa.Integer(), nullable=False),
        sa.Column("virtual_departure_service_minute", sa.Integer(), nullable=False),
        sa.Column("virtual_arrival_service_minute", sa.Integer(), nullable=False),
        sa.Column("trip_type", sa.Integer(), nullable=False),
        sa.Column("is_express", sa.Boolean(), nullable=False),
        sa.Column("vehicle_block_no", sa.Integer(), nullable=False),
        sa.Column("service_level", sa.Integer()),
        sa.CheckConstraint("sequence_no > 0", name="ck_planned_trip_sequence_positive"),
        sa.CheckConstraint("legacy_direction_number > 0", name="ck_planned_trip_legacy_direction_positive"),
        sa.CheckConstraint("vehicle_block_no > 0", name="ck_planned_trip_vehicle_block_positive"),
        sa.CheckConstraint(
            "arrival_service_minute >= departure_service_minute",
            name="ck_planned_trip_service_time_order",
        ),
        sa.CheckConstraint(
            "virtual_arrival_service_minute >= virtual_departure_service_minute",
            name="ck_planned_trip_virtual_time_order",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "plan_revision_id"],
            ["oferbus.plan_revision.organization_id", "oferbus.plan_revision.id"],
            name="fk_planned_trip_tenant_plan_revision",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("organization_id", "id", name="uq_planned_trip_org_id"),
        sa.UniqueConstraint("plan_revision_id", "sequence_no", name="uq_planned_trip_plan_sequence"),
        schema=SCHEMA,
    )

    op.create_table(
        "vehicle_block",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_revision_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("block_no", sa.Integer(), primary_key=True),
        sa.Column("trip_count", sa.Integer(), nullable=False),
        sa.Column("first_departure_service_minute", sa.Integer()),
        sa.Column("last_arrival_service_minute", sa.Integer()),
        sa.CheckConstraint("block_no > 0", name="ck_vehicle_block_block_positive"),
        sa.CheckConstraint("trip_count >= 0", name="ck_vehicle_block_trip_count_nonnegative"),
        sa.ForeignKeyConstraint(
            ["organization_id", "plan_revision_id"],
            ["oferbus.plan_revision.organization_id", "oferbus.plan_revision.id"],
            name="fk_vehicle_block_tenant_plan_revision",
            ondelete="CASCADE",
        ),
        schema=SCHEMA,
    )

    op.create_table(
        "vehicle_block_trip",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_revision_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("block_no", sa.Integer(), primary_key=True),
        sa.Column("position_no", sa.Integer(), primary_key=True),
        sa.Column("planned_trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.CheckConstraint("block_no > 0", name="ck_vehicle_block_trip_block_positive"),
        sa.CheckConstraint("position_no > 0", name="ck_vehicle_block_trip_position_positive"),
        sa.ForeignKeyConstraint(
            ["organization_id", "plan_revision_id", "block_no"],
            [
                "oferbus.vehicle_block.organization_id",
                "oferbus.vehicle_block.plan_revision_id",
                "oferbus.vehicle_block.block_no",
            ],
            name="fk_vehicle_block_trip_tenant_block",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "planned_trip_id"],
            ["oferbus.planned_trip.organization_id", "oferbus.planned_trip.id"],
            name="fk_vehicle_block_trip_tenant_trip",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("plan_revision_id", "planned_trip_id", name="uq_vehicle_block_trip_plan_trip"),
        schema=SCHEMA,
    )

    op.create_table(
        "result_snapshot",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("computation_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("output_fingerprint", sa.String(128), nullable=False),
        sa.Column("total_passengers", sa.Integer(), nullable=False),
        sa.Column("total_trips", sa.Integer(), nullable=False),
        sa.Column("mean_extension_km", sa.Numeric(14, 6), nullable=False),
        sa.Column("total_distance_km", sa.Numeric(14, 6), nullable=False),
        sa.Column("effective_fleet", sa.Integer(), nullable=False),
        sa.Column("mean_daily_distance_per_vehicle_km", sa.Numeric(14, 6), nullable=False),
        sa.Column("mean_passengers_per_trip", sa.Numeric(14, 6), nullable=False),
        sa.Column("mean_critical_passengers_per_trip", sa.Numeric(14, 6), nullable=False),
        sa.Column("mean_occupancy_rate", sa.Numeric(14, 8)),
        sa.Column("passengers_per_km", sa.Numeric(14, 8), nullable=False),
        sa.Column("daily_total_cost", sa.Numeric(16, 6), nullable=False),
        sa.Column("mean_cost_per_vehicle", sa.Numeric(16, 6), nullable=False),
        sa.Column("cost_per_trip", sa.Numeric(16, 6), nullable=False),
        sa.Column("cost_per_equivalent_passenger", sa.Numeric(16, 8), nullable=False),
        sa.Column("mean_trips_per_vehicle", sa.Numeric(14, 6), nullable=False),
        sa.Column("mean_travel_time_min", sa.Numeric(14, 6), nullable=False),
        sa.Column("mean_speed_kmh", sa.Numeric(14, 6), nullable=False),
        sa.Column("distance_semantics", sa.Text(), nullable=False),
        sa.Column("provenance_notes", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("total_passengers >= 0", name="ck_result_snapshot_total_passengers_nonnegative"),
        sa.CheckConstraint("total_trips >= 0", name="ck_result_snapshot_total_trips_nonnegative"),
        sa.CheckConstraint("effective_fleet >= 0", name="ck_result_snapshot_effective_fleet_nonnegative"),
        sa.ForeignKeyConstraint(
            ["organization_id", "plan_revision_id"],
            ["oferbus.plan_revision.organization_id", "oferbus.plan_revision.id"],
            name="fk_result_snapshot_tenant_plan_revision",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "computation_run_id"],
            ["oferbus.computation_run.organization_id", "oferbus.computation_run.id"],
            name="fk_result_snapshot_tenant_computation_run",
        ),
        sa.UniqueConstraint("organization_id", "id", name="uq_result_snapshot_org_id"),
        sa.UniqueConstraint("plan_revision_id", name="uq_result_snapshot_plan_revision"),
        sa.UniqueConstraint("computation_run_id", name="uq_result_snapshot_computation_run"),
        schema=SCHEMA,
    )

    op.create_index(
        "ix_planned_trip_plan_departure",
        "planned_trip",
        ["plan_revision_id", "departure_service_minute", "sequence_no"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_plan_revision_scenario_revision",
        "plan_revision",
        ["scenario_revision_id", "revision_no"],
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_index("ix_plan_revision_scenario_revision", table_name="plan_revision", schema=SCHEMA)
    op.drop_index("ix_planned_trip_plan_departure", table_name="planned_trip", schema=SCHEMA)
    op.drop_table("result_snapshot", schema=SCHEMA)
    op.drop_table("vehicle_block_trip", schema=SCHEMA)
    op.drop_table("vehicle_block", schema=SCHEMA)
    op.drop_table("planned_trip", schema=SCHEMA)
    op.drop_table("plan_revision", schema=SCHEMA)
