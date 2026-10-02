from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class PlanRevision(Base):
    __tablename__ = "plan_revision"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    scenario_revision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    computation_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    parent_plan_revision_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    revision_no: Mapped[int] = mapped_column(Integer, nullable=False)
    source_kind: Mapped[str] = mapped_column(String(32), nullable=False, default="computed")
    semantic_layer: Mapped[str] = mapped_column(String(32), nullable=False)
    engine_id: Mapped[str] = mapped_column(String(80), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(80), nullable=False)
    input_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    output_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("organization_id", "id", name="uq_plan_revision_org_id"),
        UniqueConstraint("scenario_revision_id", "revision_no", name="uq_plan_revision_scenario_revision_no"),
        UniqueConstraint("computation_run_id", name="uq_plan_revision_computation_run"),
        CheckConstraint("revision_no > 0", name="revision_positive"),
        CheckConstraint("source_kind IN ('computed','manual')", name="source_kind_valid"),
        CheckConstraint("semantic_layer IN ('legacy-exact','normalized','modern')", name="semantic_layer_valid"),
        ForeignKeyConstraint(
            ["organization_id", "scenario_revision_id"],
            ["oferbus.scenario_revision.organization_id", "oferbus.scenario_revision.id"],
            name="fk_plan_revision_tenant_scenario_revision",
        ),
        ForeignKeyConstraint(
            ["organization_id", "computation_run_id"],
            ["oferbus.computation_run.organization_id", "oferbus.computation_run.id"],
            name="fk_plan_revision_tenant_computation_run",
        ),
        ForeignKeyConstraint(
            ["organization_id", "parent_plan_revision_id"],
            ["oferbus.plan_revision.organization_id", "oferbus.plan_revision.id"],
            name="fk_plan_revision_tenant_parent",
        ),
    )


class PlannedTrip(Base):
    __tablename__ = "planned_trip"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    plan_revision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    direction_key: Mapped[str] = mapped_column(String(64), nullable=False)
    legacy_direction_number: Mapped[int] = mapped_column(Integer, nullable=False)
    departure_service_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    arrival_service_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    virtual_departure_service_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    virtual_arrival_service_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    trip_type: Mapped[int] = mapped_column(Integer, nullable=False)
    is_express: Mapped[bool] = mapped_column(Boolean, nullable=False)
    vehicle_block_no: Mapped[int] = mapped_column(Integer, nullable=False)
    service_level: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        UniqueConstraint("organization_id", "id", name="uq_planned_trip_org_id"),
        UniqueConstraint("plan_revision_id", "sequence_no", name="uq_planned_trip_plan_sequence"),
        CheckConstraint("sequence_no > 0", name="sequence_positive"),
        CheckConstraint("legacy_direction_number > 0", name="legacy_direction_positive"),
        CheckConstraint("vehicle_block_no >= 0", name="vehicle_block_nonnegative"),
        CheckConstraint("arrival_service_minute >= departure_service_minute", name="service_time_order"),
        CheckConstraint(
            "virtual_arrival_service_minute >= virtual_departure_service_minute",
            name="virtual_time_order",
        ),
        ForeignKeyConstraint(
            ["organization_id", "plan_revision_id"],
            ["oferbus.plan_revision.organization_id", "oferbus.plan_revision.id"],
            name="fk_planned_trip_tenant_plan_revision",
            ondelete="CASCADE",
        ),
    )


class VehicleBlock(Base):
    __tablename__ = "vehicle_block"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    plan_revision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    block_no: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_count: Mapped[int] = mapped_column(Integer, nullable=False)
    first_departure_service_minute: Mapped[int | None] = mapped_column(Integer)
    last_arrival_service_minute: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        CheckConstraint("block_no > 0", name="block_positive"),
        CheckConstraint("trip_count >= 0", name="trip_count_nonnegative"),
        ForeignKeyConstraint(
            ["organization_id", "plan_revision_id"],
            ["oferbus.plan_revision.organization_id", "oferbus.plan_revision.id"],
            name="fk_vehicle_block_tenant_plan_revision",
            ondelete="CASCADE",
        ),
    )


class VehicleBlockTrip(Base):
    __tablename__ = "vehicle_block_trip"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    plan_revision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    block_no: Mapped[int] = mapped_column(Integer, primary_key=True)
    position_no: Mapped[int] = mapped_column(Integer, primary_key=True)
    planned_trip_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("plan_revision_id", "planned_trip_id", name="uq_vehicle_block_trip_plan_trip"),
        CheckConstraint("block_no > 0", name="block_positive"),
        CheckConstraint("position_no > 0", name="position_positive"),
        ForeignKeyConstraint(
            ["organization_id", "plan_revision_id", "block_no"],
            [
                "oferbus.vehicle_block.organization_id",
                "oferbus.vehicle_block.plan_revision_id",
                "oferbus.vehicle_block.block_no",
            ],
            name="fk_vehicle_block_trip_tenant_block",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["organization_id", "planned_trip_id"],
            ["oferbus.planned_trip.organization_id", "oferbus.planned_trip.id"],
            name="fk_vehicle_block_trip_tenant_trip",
            ondelete="CASCADE",
        ),
    )


class ResultSnapshot(Base):
    __tablename__ = "result_snapshot"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    plan_revision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    computation_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    output_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    total_passengers: Mapped[int] = mapped_column(Integer, nullable=False)
    total_trips: Mapped[int] = mapped_column(Integer, nullable=False)
    mean_extension_km: Mapped[Decimal] = mapped_column(Numeric(14, 6), nullable=False)
    total_distance_km: Mapped[Decimal] = mapped_column(Numeric(14, 6), nullable=False)
    effective_fleet: Mapped[int] = mapped_column(Integer, nullable=False)
    mean_daily_distance_per_vehicle_km: Mapped[Decimal] = mapped_column(Numeric(14, 6), nullable=False)
    mean_passengers_per_trip: Mapped[Decimal] = mapped_column(Numeric(14, 6), nullable=False)
    mean_critical_passengers_per_trip: Mapped[Decimal] = mapped_column(Numeric(14, 6), nullable=False)
    mean_occupancy_rate: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    passengers_per_km: Mapped[Decimal] = mapped_column(Numeric(14, 8), nullable=False)
    daily_total_cost: Mapped[Decimal] = mapped_column(Numeric(16, 6), nullable=False)
    mean_cost_per_vehicle: Mapped[Decimal] = mapped_column(Numeric(16, 6), nullable=False)
    cost_per_trip: Mapped[Decimal] = mapped_column(Numeric(16, 6), nullable=False)
    cost_per_equivalent_passenger: Mapped[Decimal] = mapped_column(Numeric(16, 8), nullable=False)
    mean_trips_per_vehicle: Mapped[Decimal] = mapped_column(Numeric(14, 6), nullable=False)
    mean_travel_time_min: Mapped[Decimal] = mapped_column(Numeric(14, 6), nullable=False)
    mean_speed_kmh: Mapped[Decimal] = mapped_column(Numeric(14, 6), nullable=False)
    distance_semantics: Mapped[str] = mapped_column(Text, nullable=False)
    provenance_notes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("organization_id", "id", name="uq_result_snapshot_org_id"),
        UniqueConstraint("plan_revision_id", name="uq_result_snapshot_plan_revision"),
        UniqueConstraint("computation_run_id", name="uq_result_snapshot_computation_run"),
        CheckConstraint("total_passengers >= 0", name="total_passengers_nonnegative"),
        CheckConstraint("total_trips >= 0", name="total_trips_nonnegative"),
        CheckConstraint("effective_fleet >= 0", name="effective_fleet_nonnegative"),
        ForeignKeyConstraint(
            ["organization_id", "plan_revision_id"],
            ["oferbus.plan_revision.organization_id", "oferbus.plan_revision.id"],
            name="fk_result_snapshot_tenant_plan_revision",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["organization_id", "computation_run_id"],
            ["oferbus.computation_run.organization_id", "oferbus.computation_run.id"],
            name="fk_result_snapshot_tenant_computation_run",
        ),
    )
