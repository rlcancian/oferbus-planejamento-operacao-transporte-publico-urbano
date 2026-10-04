"""Align persisted typed edit commands with promoted Phase C operations.

Revision ID: 0007_plan_edit_command_types
Revises: 0006_plan_editing
Create Date: 2026-10-04
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0007_plan_edit_command_types"
down_revision: Union[str, Sequence[str], None] = "0006_plan_editing"
branch_labels = None
depends_on = None

SCHEMA = "oferbus"


def upgrade() -> None:
    op.drop_constraint("ck_plan_edit_command_type_valid", "plan_edit_command", schema=SCHEMA, type_="check")
    op.create_check_constraint(
        "ck_plan_edit_command_type_valid",
        "plan_edit_command",
        "command_type IN ('fork', 'move-trip', 'set-trip-express')",
        schema=SCHEMA,
    )


def downgrade() -> None:
    # A downgrade is intentionally fail-safe: PostgreSQL will reject it if
    # promoted command rows exist instead of silently destroying journal data.
    op.drop_constraint("ck_plan_edit_command_type_valid", "plan_edit_command", schema=SCHEMA, type_="check")
    op.create_check_constraint(
        "ck_plan_edit_command_type_valid",
        "plan_edit_command",
        "command_type IN ('fork')",
        schema=SCHEMA,
    )
