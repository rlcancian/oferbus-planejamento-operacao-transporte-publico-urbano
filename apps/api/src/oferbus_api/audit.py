from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from oferbus_db import AuditEvent

from .identity import Principal


def record_audit_event(
    session: Session,
    principal: Principal,
    *,
    event_type: str,
    entity_type: str,
    entity_id: uuid.UUID | None = None,
    correlation_id: str | None = None,
    details: dict | None = None,
) -> AuditEvent:
    """Stage an audit event in the caller's transaction.

    The caller owns commit/rollback. This keeps domain mutation and its audit
    record atomic once write endpoints are introduced.
    """
    event = AuditEvent(
        organization_id=principal.organization_id,
        actor_user_id=principal.user_id,
        actor_subject=principal.subject,
        actor_role_key=principal.role.value,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        correlation_id=correlation_id,
        details=details or {},
    )
    session.add(event)
    return event
