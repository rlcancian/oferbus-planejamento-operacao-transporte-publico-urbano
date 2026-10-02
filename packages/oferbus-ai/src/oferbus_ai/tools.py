from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Callable, Protocol

from .contracts import LLMToolDefinition


class ToolRisk(StrEnum):
    READ = "read"
    COMPUTE = "compute"
    MUTATE = "mutate"
    ADMIN = "admin"


class ConfirmationPolicy(StrEnum):
    NONE = "none"
    REQUIRED = "required"


@dataclass(frozen=True)
class ToolContext:
    user_id: uuid.UUID
    organization_id: uuid.UUID
    subject: str
    role: str
    permissions: frozenset[str]
    correlation_id: str


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    required_permission: str
    risk: ToolRisk = ToolRisk.READ
    confirmation: ConfirmationPolicy = ConfirmationPolicy.NONE

    def as_llm_definition(self) -> LLMToolDefinition:
        return LLMToolDefinition(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
        )


@dataclass(frozen=True)
class ToolExecution:
    tool_name: str
    output: dict[str, Any]
    correlation_id: str


class ToolError(RuntimeError):
    pass


class ToolNotFoundError(ToolError):
    pass


class ToolPermissionError(ToolError):
    pass


class ToolConfirmationRequiredError(ToolError):
    pass


ToolHandler = Callable[[ToolContext, dict[str, Any]], dict[str, Any]]


class AuditSink(Protocol):
    def record(
        self,
        *,
        context: ToolContext,
        tool: ToolSpec,
        outcome: str,
        argument_keys: tuple[str, ...],
        details: dict[str, Any] | None = None,
    ) -> None: ...


class NullAuditSink:
    def record(
        self,
        *,
        context: ToolContext,
        tool: ToolSpec,
        outcome: str,
        argument_keys: tuple[str, ...],
        details: dict[str, Any] | None = None,
    ) -> None:
        return None


@dataclass
class _RegisteredTool:
    spec: ToolSpec
    handler: ToolHandler


@dataclass
class ToolRegistry:
    audit_sink: AuditSink = field(default_factory=NullAuditSink)
    _tools: dict[str, _RegisteredTool] = field(default_factory=dict)

    def register(self, spec: ToolSpec, handler: ToolHandler) -> None:
        if spec.name in self._tools:
            raise ValueError(f"Tool already registered: {spec.name}")
        self._tools[spec.name] = _RegisteredTool(spec=spec, handler=handler)

    def specs_for_permissions(self, permissions: frozenset[str]) -> tuple[ToolSpec, ...]:
        return tuple(
            registered.spec
            for _, registered in sorted(self._tools.items())
            if registered.spec.required_permission in permissions
        )

    def llm_definitions_for_permissions(self, permissions: frozenset[str]) -> tuple[LLMToolDefinition, ...]:
        return tuple(spec.as_llm_definition() for spec in self.specs_for_permissions(permissions))

    def get_spec(self, tool_name: str) -> ToolSpec:
        registered = self._tools.get(tool_name)
        if registered is None:
            raise ToolNotFoundError(f"Unknown tool: {tool_name}")
        return registered.spec

    def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        context: ToolContext,
        *,
        confirmed: bool = False,
    ) -> ToolExecution:
        registered = self._tools.get(tool_name)
        if registered is None:
            raise ToolNotFoundError(f"Unknown tool: {tool_name}")

        spec = registered.spec
        argument_keys = tuple(sorted(arguments))

        if spec.required_permission not in context.permissions:
            self.audit_sink.record(
                context=context,
                tool=spec,
                outcome="denied",
                argument_keys=argument_keys,
                details={"reason": "missing-permission"},
            )
            raise ToolPermissionError(f"Missing permission: {spec.required_permission}")

        if spec.confirmation == ConfirmationPolicy.REQUIRED and not confirmed:
            self.audit_sink.record(
                context=context,
                tool=spec,
                outcome="confirmation-required",
                argument_keys=argument_keys,
            )
            raise ToolConfirmationRequiredError(f"Confirmation required for tool: {tool_name}")

        try:
            output = registered.handler(context, arguments)
        except Exception as exc:
            self.audit_sink.record(
                context=context,
                tool=spec,
                outcome="failed",
                argument_keys=argument_keys,
                details={"error_type": type(exc).__name__},
            )
            raise

        self.audit_sink.record(
            context=context,
            tool=spec,
            outcome="succeeded",
            argument_keys=argument_keys,
        )
        return ToolExecution(
            tool_name=tool_name,
            output=output,
            correlation_id=context.correlation_id,
        )
