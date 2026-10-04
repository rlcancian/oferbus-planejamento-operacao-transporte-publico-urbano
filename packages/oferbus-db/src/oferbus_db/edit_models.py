from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class PlanEditCommand(Base):
    """Immutable journal entry for one version-producing plan edit command."""

    __tablename__ = "plan_edit_command"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    client_command_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    parent_plan_revision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    derived_plan_revision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    command_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("oferbus.app_user.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("organization_id", "id", name="uq_plan_edit_command_org_id"),
        UniqueConstraint("organization_id", "client_command_id", name="uq_plan_edit_command_client_id"),
        UniqueConstraint("derived_plan_revision_id", name="uq_plan_edit_command_derived_revision"),
        CheckConstraint(
            "command_type IN ('fork', 'move-trip', 'set-trip-express')",
            name="plan_edit_command_type_valid",
        ),
        ForeignKeyConstraint(
            ["organization_id", "parent_plan_revision_id"],
            ["oferbus.plan_revision.organization_id", "oferbus.plan_revision.id"],
            name="fk_plan_edit_command_tenant_parent",
        ),
        ForeignKeyConstraint(
            ["organization_id", "derived_plan_revision_id"],
            ["oferbus.plan_revision.organization_id", "oferbus.plan_revision.id"],
            name="fk_plan_edit_command_tenant_derived",
        ),
    )
