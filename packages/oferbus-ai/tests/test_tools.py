import uuid

import pytest

from oferbus_ai import (
    ConfirmationPolicy,
    ToolConfirmationRequiredError,
    ToolContext,
    ToolNotFoundError,
    ToolPermissionError,
    ToolRegistry,
    ToolRisk,
    ToolSpec,
)


class RecordingAuditSink:
    def __init__(self) -> None:
        self.events: list[tuple[str, str]] = []

    def record(self, *, context, tool, outcome, argument_keys, details=None) -> None:
        self.events.append((tool.name, outcome))


def context(*permissions: str) -> ToolContext:
    return ToolContext(
        user_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        subject="test:user",
        role="planner",
        permissions=frozenset(permissions),
        correlation_id="test-correlation",
    )


def test_registry_exposes_only_authorized_tools() -> None:
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            name="read.status",
            description="Read status",
            input_schema={"type": "object", "properties": {}},
            required_permission="result:read",
        ),
        lambda ctx, args: {"ok": True},
    )
    registry.register(
        ToolSpec(
            name="compute.run",
            description="Run computation",
            input_schema={"type": "object", "properties": {}},
            required_permission="computation:run",
            risk=ToolRisk.COMPUTE,
            confirmation=ConfirmationPolicy.REQUIRED,
        ),
        lambda ctx, args: {"queued": True},
    )

    specs = registry.specs_for_permissions(frozenset({"result:read"}))
    assert [spec.name for spec in specs] == ["read.status"]


def test_compute_tool_requires_confirmation() -> None:
    audit = RecordingAuditSink()
    registry = ToolRegistry(audit_sink=audit)
    registry.register(
        ToolSpec(
            name="compute.run",
            description="Run computation",
            input_schema={"type": "object", "properties": {}},
            required_permission="computation:run",
            risk=ToolRisk.COMPUTE,
            confirmation=ConfirmationPolicy.REQUIRED,
        ),
        lambda ctx, args: {"queued": True},
    )

    with pytest.raises(ToolConfirmationRequiredError):
        registry.execute("compute.run", {}, context("computation:run"))

    result = registry.execute("compute.run", {}, context("computation:run"), confirmed=True)
    assert result.output == {"queued": True}
    assert audit.events == [
        ("compute.run", "confirmation-required"),
        ("compute.run", "succeeded"),
    ]


def test_missing_permission_is_denied_and_audited() -> None:
    audit = RecordingAuditSink()
    registry = ToolRegistry(audit_sink=audit)
    registry.register(
        ToolSpec(
            name="read.status",
            description="Read status",
            input_schema={"type": "object", "properties": {}},
            required_permission="result:read",
        ),
        lambda ctx, args: {"ok": True},
    )

    with pytest.raises(ToolPermissionError):
        registry.execute("read.status", {}, context())

    assert audit.events == [("read.status", "denied")]


def test_unknown_tool_is_not_dispatchable() -> None:
    with pytest.raises(ToolNotFoundError):
        ToolRegistry().execute("sql.execute", {"sql": "drop table x"}, context("organization:read"))
