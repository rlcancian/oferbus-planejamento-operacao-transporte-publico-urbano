from sqlalchemy import ForeignKeyConstraint, UniqueConstraint

from oferbus_db import Base


def test_audit_event_is_tenant_owned_and_preserves_actor_context() -> None:
    table = Base.metadata.tables["oferbus.audit_event"]

    assert {"organization_id", "actor_user_id", "actor_subject", "actor_role_key", "correlation_id"} <= set(table.c.keys())
    assert any(
        isinstance(constraint, UniqueConstraint)
        and {column.name for column in constraint.columns} == {"organization_id", "id"}
        for constraint in table.constraints
    )


def test_audit_event_references_organization_and_actor() -> None:
    table = Base.metadata.tables["oferbus.audit_event"]
    targets = {
        element.target_fullname
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
        for element in constraint.elements
    }

    assert "oferbus.organization.id" in targets
    assert "oferbus.app_user.id" in targets
