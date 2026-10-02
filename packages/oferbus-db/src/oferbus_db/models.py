from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
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


class Organization(Base):
    __tablename__ = "organization"
    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    organization_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AppUser(Base):
    __tablename__ = "app_user"
    id: Mapped[uuid.UUID] = uuid_pk()
    display_name: Mapped[str] = mapped_column(String(240), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320))
    external_subject: Mapped[str | None] = mapped_column(String(320), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class OrganizationMembership(Base):
    __tablename__ = "organization_membership"
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("oferbus.organization.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("oferbus.app_user.id", ondelete="CASCADE"), primary_key=True)
    role_key: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    __table_args__ = (UniqueConstraint("organization_id", "user_id", name="uq_membership_org_user"),)


class Municipality(Base):
    __tablename__ = "municipality"
    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = organization_fk()
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    state_region: Mapped[str | None] = mapped_column(String(120))
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, default="BR")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    __table_args__ = (UniqueConstraint("organization_id", "id", name="uq_municipality_org_id"),)


class TransitOperator(Base):
    __tablename__ = "transit_operator"
    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = organization_fk()
    municipality_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    __table_args__ = (
        UniqueConstraint("organization_id", "id", name="uq_transit_operator_org_id"),
        ForeignKeyConstraint(["organization_id", "municipality_id"], ["oferbus.municipality.organization_id", "oferbus.municipality.id"], name="fk_transit_operator_tenant_municipality"),
    )


class Terminal(Base):
    __tablename__ = "terminal"
    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = organization_fk()
    municipality_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    allows_storage: Mapped[bool | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    __table_args__ = (
        UniqueConstraint("organization_id", "id", name="uq_terminal_org_id"),
        ForeignKeyConstraint(["organization_id", "municipality_id"], ["oferbus.municipality.organization_id", "oferbus.municipality.id"], name="fk_terminal_tenant_municipality"),
    )


class TransitLine(Base):
    __tablename__ = "transit_line"
    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = organization_fk()
    municipality_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    operator_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    public_code: Mapped[str | None] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    legacy_operation_type_code: Mapped[int | None]
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("organization_id", "id", name="uq_transit_line_org_id"),
        ForeignKeyConstraint(["organization_id", "municipality_id"], ["oferbus.municipality.organization_id", "oferbus.municipality.id"], name="fk_transit_line_tenant_municipality"),
        ForeignKeyConstraint(["organization_id", "operator_id"], ["oferbus.transit_operator.organization_id", "oferbus.transit_operator.id"], name="fk_transit_line_tenant_operator"),
    )


class LineDirection(Base):
    __tablename__ = "line_direction"
    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = organization_fk()
    line_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    direction_key: Mapped[str] = mapped_column(String(64), nullable=False)
    origin_terminal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    destination_terminal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    extension_km: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    legacy_direction_number: Mapped[int | None]
    __table_args__ = (
        UniqueConstraint("organization_id", "id", name="uq_line_direction_org_id"),
        UniqueConstraint("line_id", "direction_key", name="uq_line_direction_line_key"),
        CheckConstraint("extension_km IS NULL OR extension_km >= 0", name="extension_nonnegative"),
        ForeignKeyConstraint(["organization_id", "line_id"], ["oferbus.transit_line.organization_id", "oferbus.transit_line.id"], name="fk_line_direction_tenant_line"),
        ForeignKeyConstraint(["organization_id", "origin_terminal_id"], ["oferbus.terminal.organization_id", "oferbus.terminal.id"], name="fk_line_direction_tenant_origin_terminal"),
        ForeignKeyConstraint(["organization_id", "destination_terminal_id"], ["oferbus.terminal.organization_id", "oferbus.terminal.id"], name="fk_line_direction_tenant_destination_terminal"),
    )


class PlanningProject(Base):
    __tablename__ = "planning_project"
    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = organization_fk()
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("oferbus.app_user.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("organization_id", "id", name="uq_planning_project_org_id"),)


class ProjectLine(Base):
    __tablename__ = "project_line"
    organization_id: Mapped[uuid.UUID] = organization_fk()
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    line_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    __table_args__ = (
        ForeignKeyConstraint(["organization_id", "project_id"], ["oferbus.planning_project.organization_id", "oferbus.planning_project.id"], name="fk_project_line_tenant_project"),
        ForeignKeyConstraint(["organization_id", "line_id"], ["oferbus.transit_line.organization_id", "oferbus.transit_line.id"], name="fk_project_line_tenant_line"),
    )


class Scenario(Base):
    __tablename__ = "scenario"
    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = organization_fk()
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("oferbus.app_user.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("organization_id", "id", name="uq_scenario_org_id"),
        ForeignKeyConstraint(["organization_id", "project_id"], ["oferbus.planning_project.organization_id", "oferbus.planning_project.id"], name="fk_scenario_tenant_project"),
    )


class ScenarioRevision(Base):
    __tablename__ = "scenario_revision"
    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = organization_fk()
    scenario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    revision_no: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_revision_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("oferbus.app_user.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    reason: Mapped[str | None] = mapped_column(Text)
    input_fingerprint: Mapped[str | None] = mapped_column(String(128))
    __table_args__ = (
        UniqueConstraint("organization_id", "id", name="uq_scenario_revision_org_id"),
        UniqueConstraint("scenario_id", "revision_no", name="uq_scenario_revision_number"),
        CheckConstraint("revision_no > 0", name="revision_positive"),
        ForeignKeyConstraint(["organization_id", "scenario_id"], ["oferbus.scenario.organization_id", "oferbus.scenario.id"], name="fk_scenario_revision_tenant_scenario"),
        ForeignKeyConstraint(["organization_id", "parent_revision_id"], ["oferbus.scenario_revision.organization_id", "oferbus.scenario_revision.id"], name="fk_scenario_revision_tenant_parent"),
    )


class ComputationRun(Base):
    __tablename__ = "computation_run"
    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = organization_fk()
    scenario_revision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    run_kind: Mapped[str] = mapped_column(String(80), nullable=False)
    semantic_layer: Mapped[str] = mapped_column(String(32), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(80), nullable=False)
    engine_source_revision: Mapped[str | None] = mapped_column(String(80))
    deterministic_seed: Mapped[int | None] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    input_fingerprint: Mapped[str | None] = mapped_column(String(128))
    output_fingerprint: Mapped[str | None] = mapped_column(String(128))
    diagnostics: Mapped[dict | None] = mapped_column(JSONB)
    __table_args__ = (
        UniqueConstraint("organization_id", "id", name="uq_computation_run_org_id"),
        CheckConstraint("semantic_layer IN ('legacy-exact','normalized','modern')", name="semantic_layer_valid"),
        ForeignKeyConstraint(["organization_id", "scenario_revision_id"], ["oferbus.scenario_revision.organization_id", "oferbus.scenario_revision.id"], name="fk_computation_run_tenant_scenario_revision"),
    )
