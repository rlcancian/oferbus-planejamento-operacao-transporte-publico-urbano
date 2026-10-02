import os
import uuid

import pytest
from fastapi import HTTPException, Request

from oferbus_api.identity import (
    DevelopmentHeaderIdentityAdapter,
    Permission,
    Principal,
    Role,
    parse_organization_id,
)


def _request(headers: dict[str, str]) -> Request:
    encoded_headers = [(key.lower().encode(), value.encode()) for key, value in headers.items()]
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": encoded_headers,
            "client": ("127.0.0.1", 12345),
            "server": ("127.0.0.1", 8010),
        }
    )


def test_development_header_adapter_reads_external_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OFERBUS_ENV", "development")
    request = _request(
        {
            "x-oferbus-subject": "dev:rafael",
            "x-oferbus-display-name": "Rafael",
            "x-oferbus-email": "rafael@example.invalid",
        }
    )

    claims = DevelopmentHeaderIdentityAdapter().authenticate(request)

    assert claims is not None
    assert claims.subject == "dev:rafael"
    assert claims.display_name == "Rafael"


def test_development_header_adapter_is_forbidden_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OFERBUS_ENV", "production")
    request = _request({"x-oferbus-subject": "dev:forbidden"})

    with pytest.raises(RuntimeError, match="forbidden in production"):
        DevelopmentHeaderIdentityAdapter().authenticate(request)


def test_organization_context_requires_valid_uuid() -> None:
    with pytest.raises(HTTPException) as missing:
        parse_organization_id(_request({}))
    assert missing.value.status_code == 400

    with pytest.raises(HTTPException) as invalid:
        parse_organization_id(_request({"x-oferbus-organization-id": "not-a-uuid"}))
    assert invalid.value.status_code == 400


def test_role_permission_matrix_is_monotonic_for_core_planning_capabilities() -> None:
    principal = Principal(
        user_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        subject="test:planner",
        display_name="Planner",
        role=Role.PLANNER,
    )

    assert principal.has_permission(Permission.PROJECT_WRITE)
    assert principal.has_permission(Permission.SCENARIO_WRITE)
    assert principal.has_permission(Permission.COMPUTATION_RUN)
    assert principal.has_permission(Permission.PLAN_EDIT)
    assert not principal.has_permission(Permission.MEMBERSHIP_MANAGE)
    assert not principal.has_permission(Permission.ORGANIZATION_ADMIN)


def test_viewer_cannot_mutate_planning_domain() -> None:
    principal = Principal(
        user_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        subject="test:viewer",
        display_name="Viewer",
        role=Role.VIEWER,
    )

    assert principal.has_permission(Permission.PROJECT_READ)
    assert principal.has_permission(Permission.RESULT_READ)
    assert not principal.has_permission(Permission.PROJECT_WRITE)
    assert not principal.has_permission(Permission.COMPUTATION_RUN)
    assert not principal.has_permission(Permission.PLAN_EDIT)
