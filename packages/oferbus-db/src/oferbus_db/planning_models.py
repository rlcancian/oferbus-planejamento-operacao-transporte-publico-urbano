from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
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


def uuid_pk():
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def organization_fk():
    return mapped_column(
        UUID(as_uuid=True),
        ForeignKey("oferbus.organization.id", ondelete="RESTRICT"),
        nullable=False,
    )


class ObservedTripDataset(Base):
    __tablename__ = "observed_trip_dataset"

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = organization_fk()
    line_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("oferbus.app_user.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "id", name="uq_observed_trip_dataset_org_id"),
        ForeignKeyConstraint(
            ["organization_id", "line_id"],
            ["oferbus.transit_line.organization_id", "oferbus.transit_line.id"],
            name="fk_observed_trip_dataset_tenant_line",
        ),
    )


class ObservedTripDatasetRevision(Base):
    __tablename__ = "observed_trip_dataset_revision"

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = organization_fk()
    dataset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    revision_no: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_revision_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    source_label: Mapped[str | None] = mapped_column(String(240))
    source_metadata: Mapped[dict | None] = mapped_column(JSONB)
    content_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("oferbus.app_user.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "id", name="uq_observed_trip_dataset_revision_org_id"),
        UniqueConstraint("dataset_id", "revision_no", name="uq_observed_trip_dataset_revision_number"),
        CheckConstraint("revision_no > 0", name="observed_revision_positive"),
        ForeignKeyConstraint(
            ["organization_id", "dataset_id"],
            ["oferbus.observed_trip_dataset.organization_id", "oferbus.observed_trip_dataset.id"],
            name="fk_observed_trip_dataset_revision_tenant_dataset",
        ),
        ForeignKeyConstraint(
            ["organization_id", "parent_revision_id"],
            ["oferbus.observed_trip_dataset_revision.organization_id", "oferbus.observed_trip_dataset_revision.id"],
            name="fk_observed_trip_dataset_revision_tenant_parent",
        ),
    )


class ObservedTripObservation(Base):
    __tablename__ = "observed_trip_observation"

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = organization_fk()
    dataset_revision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    direction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    departure_service_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    passengers: Mapped[int] = mapped_column(Integer, nullable=False)
    critical_passengers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    travel_time_min: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint(
            "dataset_revision_id",
            "direction_id",
            "sequence_no",
            name="uq_observed_trip_observation_sequence",
        ),
        CheckConstraint("sequence_no > 0", name="observed_sequence_positive"),
        CheckConstraint("departure_service_minute >= 0", name="observed_departure_nonnegative"),
        CheckConstraint("passengers >= 0", name="observed_passengers_nonnegative"),
        CheckConstraint("critical_passengers >= 0", name="observed_critical_passengers_nonnegative"),
        CheckConstraint("travel_time_min >= 0", name="observed_travel_time_nonnegative"),
        ForeignKeyConstraint(
            ["organization_id", "dataset_revision_id"],
            [
                "oferbus.observed_trip_dataset_revision.organization_id",
                "oferbus.observed_trip_dataset_revision.id",
            ],
            name="fk_observed_trip_observation_tenant_revision",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["organization_id", "direction_id"],
            ["oferbus.line_direction.organization_id", "oferbus.line_direction.id"],
            name="fk_observed_trip_observation_tenant_direction",
        ),
    )


class ScenarioPlanningInput(Base):
    __tablename__ = "scenario_planning_input"

    organization_id: Mapped[uuid.UUID] = organization_fk()
    scenario_revision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    semantic_layer: Mapped[str] = mapped_column(String(32), nullable=False)

    vehicle_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    vehicle_free_area_m2: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    vehicle_capacity_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    cost_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="per_km")
    cost_per_km: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False, default=0)
    fixed_cost_per_vehicle: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False, default=0)
    variable_cost_per_km: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False, default=0)

    max_headway_min: Mapped[int] = mapped_column(Integer, nullable=False)
    project_capacity_passengers: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    valley_capacity_passengers: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    boarding_seconds_per_passenger: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    alighting_seconds_per_passenger: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    radial: Mapped[bool] = mapped_column(Boolean, nullable=False)
    create_express_returns: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mean_renewal_index: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False, default=1)
    typical_day_participation: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False, default=1)
    equivalent_passenger_index: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "scenario_revision_id", name="uq_scenario_planning_input_org_revision"),
        CheckConstraint(
            "semantic_layer IN ('legacy-exact','normalized','modern')",
            name="scenario_planning_semantic_layer_valid",
        ),
        CheckConstraint("vehicle_seats >= 0", name="scenario_planning_vehicle_seats_nonnegative"),
        CheckConstraint("vehicle_free_area_m2 > 0", name="scenario_planning_vehicle_area_positive"),
        CheckConstraint("vehicle_capacity_level >= 0", name="scenario_planning_capacity_level_nonnegative"),
        CheckConstraint("cost_mode IN ('per_km','fixed_variable')", name="scenario_planning_cost_mode_valid"),
        CheckConstraint("max_headway_min > 0", name="scenario_planning_headway_positive"),
        CheckConstraint("project_capacity_passengers > 0", name="scenario_planning_capacity_positive"),
        CheckConstraint("valley_capacity_passengers > 0", name="scenario_planning_valley_capacity_positive"),
        CheckConstraint("mean_renewal_index > 0", name="scenario_planning_mean_ir_positive"),
        CheckConstraint("equivalent_passenger_index > 0", name="scenario_planning_equivalent_index_positive"),
        ForeignKeyConstraint(
            ["organization_id", "scenario_revision_id"],
            ["oferbus.scenario_revision.organization_id", "oferbus.scenario_revision.id"],
            name="fk_scenario_planning_input_tenant_revision",
            ondelete="CASCADE",
        ),
    )


class ScenarioDirectionPlanningInput(Base):
    __tablename__ = "scenario_direction_planning_input"

    organization_id: Mapped[uuid.UUID] = organization_fk()
    scenario_revision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    direction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    dataset_revision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    direction_key: Mapped[str] = mapped_column(String(64), nullable=False)
    legacy_direction_number: Mapped[int] = mapped_column(Integer, nullable=False)
    service_start_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    service_end_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    demand_passengers_per_minute: Mapped[list] = mapped_column(JSONB, nullable=False)
    renewal_index_curve: Mapped[list] = mapped_column(JSONB, nullable=False)
    travel_time_min_curve: Mapped[list] = mapped_column(JSONB, nullable=False)
    demand_maximum_passengers_per_minute: Mapped[Decimal] = mapped_column(Numeric(14, 8), nullable=False)
    extension_km: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    storage_at_departure_terminal: Mapped[bool] = mapped_column(Boolean, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "scenario_revision_id",
            "legacy_direction_number",
            name="uq_scenario_direction_planning_legacy_number",
        ),
        CheckConstraint("legacy_direction_number > 0", name="scenario_direction_legacy_number_positive"),
        CheckConstraint("service_start_minute >= 0", name="scenario_direction_start_nonnegative"),
        CheckConstraint("service_end_minute >= service_start_minute", name="scenario_direction_window_valid"),
        CheckConstraint("demand_maximum_passengers_per_minute >= 0", name="scenario_direction_demand_max_nonnegative"),
        CheckConstraint("extension_km > 0", name="scenario_direction_extension_positive"),
        ForeignKeyConstraint(
            ["organization_id", "scenario_revision_id"],
            ["oferbus.scenario_revision.organization_id", "oferbus.scenario_revision.id"],
            name="fk_scenario_direction_planning_tenant_revision",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["organization_id", "direction_id"],
            ["oferbus.line_direction.organization_id", "oferbus.line_direction.id"],
            name="fk_scenario_direction_planning_tenant_direction",
        ),
        ForeignKeyConstraint(
            ["organization_id", "dataset_revision_id"],
            [
                "oferbus.observed_trip_dataset_revision.organization_id",
                "oferbus.observed_trip_dataset_revision.id",
            ],
            name="fk_scenario_direction_planning_tenant_dataset_revision",
        ),
    )
