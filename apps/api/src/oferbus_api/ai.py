from __future__ import annotations

import os
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from oferbus_ai import (
    ConfirmationPolicy,
    ToolConfirmationRequiredError,
    ToolContext,
    ToolNotFoundError,
    ToolPermissionError,
    ToolRegistry,
    ToolRisk,
    ToolSpec,
    UnconfiguredLLMProvider,
)
from oferbus_db import AuditEvent, get_session_factory
from oferbus_jobs import PostgresComputationQueue, RunSubmission

from .identity import Permission, Principal, ROLE_PERMISSIONS, require_permission


class CopilotStatusResponse(BaseModel):
    boundary: str
    provider: str
    configured: bool
    model: str | None
    direct_sql_allowed: bool


class ToolDescriptionResponse(BaseModel):
    name: str
    description: str
    required_permission: str
    risk: str
    confirmation: str
    input_schema: dict[str, Any]


class ToolExecuteRequest(BaseModel):
    arguments: dict[str, Any] = Field(default_factory=dict)
    confirmed: bool = False


class ToolExecuteResponse(BaseModel):
    tool_name: str
    correlation_id: str
    output: dict[str, Any]


class SqlAlchemyAuditSink:
    def record(self, *, context, tool, outcome, argument_keys, details=None) -> None:
        session_factory = get_session_factory()
        with session_factory() as session:
            session.add(
                AuditEvent(
                    organization_id=context.organization_id,
                    actor_user_id=context.user_id,
                    actor_subject=context.subject,
                    actor_role_key=context.role,
                    event_type=f"ai.tool.{outcome}",
                    entity_type="ai_tool",
                    correlation_id=context.correlation_id,
                    details={
                        "tool_name": tool.name,
                        "risk": tool.risk.value,
                        "confirmation_policy": tool.confirmation.value,
                        "argument_keys": list(argument_keys),
                        **(details or {}),
                    },
                )
            )
            session.commit()


def _uuid_argument(arguments: dict[str, Any], key: str) -> uuid.UUID:
    raw = arguments.get(key)
    if not isinstance(raw, str):
        raise ValueError(f"{key} must be a UUID string")
    try:
        return uuid.UUID(raw)
    except ValueError as exc:
        raise ValueError(f"{key} must be a valid UUID") from exc


def _platform_describe(context: ToolContext, arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "product": "OferBus 2026",
        "organization_id": str(context.organization_id),
        "capabilities": [
            "multi-tenant planning platform foundation",
            "versioned deterministic computation boundary",
            "asynchronous computation jobs",
            "provider-neutral AI tool boundary",
        ],
        "planning_algorithms_available_to_ai": False,
    }


def _computation_status(context: ToolContext, arguments: dict[str, Any]) -> dict[str, Any]:
    run_id = _uuid_argument(arguments, "run_id")
    snapshot = PostgresComputationQueue().get(context.organization_id, run_id)
    if snapshot is None:
        raise ValueError("computation run not found in active organization")
    return {
        "run_id": str(snapshot.run_id),
        "status": snapshot.status,
        "progress_percent": snapshot.progress_percent,
        "attempt_count": snapshot.attempt_count,
        "max_attempts": snapshot.max_attempts,
        "last_error": snapshot.last_error,
        "diagnostics": snapshot.diagnostics,
    }


def _submit_platform_smoke(context: ToolContext, arguments: dict[str, Any]) -> dict[str, Any]:
    scenario_revision_id = _uuid_argument(arguments, "scenario_revision_id")
    idempotency_key = arguments.get("idempotency_key")
    if idempotency_key is not None and not isinstance(idempotency_key, str):
        raise ValueError("idempotency_key must be a string")

    payload: dict[str, Any] = {}
    if "message" in arguments:
        payload["message"] = str(arguments["message"])
    if "delay_seconds" in arguments:
        payload["delay_seconds"] = arguments["delay_seconds"]

    snapshot = PostgresComputationQueue().submit(
        RunSubmission(
            organization_id=context.organization_id,
            scenario_revision_id=scenario_revision_id,
            submitted_by=context.user_id,
            run_kind="platform-smoke",
            semantic_layer="modern",
            engine_version="phase-a5-ai-smoke-1",
            idempotency_key=idempotency_key,
            payload=payload,
        )
    )
    return {
        "run_id": str(snapshot.run_id),
        "status": snapshot.status,
        "progress_percent": snapshot.progress_percent,
    }


def build_tool_registry() -> ToolRegistry:
    registry = ToolRegistry(audit_sink=SqlAlchemyAuditSink())
    registry.register(
        ToolSpec(
            name="platform.describe_capabilities",
            description="Describe capabilities currently materialized in the OferBus platform.",
            input_schema={"type": "object", "properties": {}, "additionalProperties": False},
            required_permission=Permission.ORGANIZATION_READ.value,
        ),
        _platform_describe,
    )
    registry.register(
        ToolSpec(
            name="computations.get_status",
            description="Read the status of a computation run in the active organization.",
            input_schema={
                "type": "object",
                "properties": {"run_id": {"type": "string", "format": "uuid"}},
                "required": ["run_id"],
                "additionalProperties": False,
            },
            required_permission=Permission.RESULT_READ.value,
        ),
        _computation_status,
    )
    registry.register(
        ToolSpec(
            name="computations.submit_platform_smoke",
            description="Submit the Phase A infrastructure smoke computation for the selected scenario revision.",
            input_schema={
                "type": "object",
                "properties": {
                    "scenario_revision_id": {"type": "string", "format": "uuid"},
                    "idempotency_key": {"type": "string", "maxLength": 160},
                    "message": {"type": "string"},
                    "delay_seconds": {"type": "number", "minimum": 0, "maximum": 3},
                },
                "required": ["scenario_revision_id"],
                "additionalProperties": False,
            },
            required_permission=Permission.COMPUTATION_RUN.value,
            risk=ToolRisk.COMPUTE,
            confirmation=ConfirmationPolicy.REQUIRED,
        ),
        _submit_platform_smoke,
    )
    return registry


def _tool_context(principal: Principal, request: Request) -> ToolContext:
    correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())
    permissions = frozenset(permission.value for permission in ROLE_PERMISSIONS[principal.role])
    return ToolContext(
        user_id=principal.user_id,
        organization_id=principal.organization_id,
        subject=principal.subject,
        role=principal.role.value,
        permissions=permissions,
        correlation_id=correlation_id,
    )


def _tool_response(spec: ToolSpec) -> ToolDescriptionResponse:
    return ToolDescriptionResponse(
        name=spec.name,
        description=spec.description,
        required_permission=spec.required_permission,
        risk=spec.risk.value,
        confirmation=spec.confirmation.value,
        input_schema=spec.input_schema,
    )


def _provider_status() -> tuple[str, bool, str | None]:
    requested = os.getenv("OFERBUS_AI_PROVIDER", "").strip().lower()
    model = os.getenv("OFERBUS_AI_MODEL", "").strip() or None
    if not requested or requested == "unconfigured":
        provider = UnconfiguredLLMProvider()
        return provider.provider_name, provider.configured, model
    return requested, False, model


router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status", response_model=CopilotStatusResponse)
def copilot_status() -> CopilotStatusResponse:
    provider, configured, model = _provider_status()
    return CopilotStatusResponse(
        boundary="ready",
        provider=provider,
        configured=configured,
        model=model,
        direct_sql_allowed=False,
    )


@router.get("/tools", response_model=list[ToolDescriptionResponse])
def list_tools(
    principal: Principal = Depends(require_permission(Permission.ORGANIZATION_READ)),
) -> list[ToolDescriptionResponse]:
    permissions = frozenset(permission.value for permission in ROLE_PERMISSIONS[principal.role])
    return [_tool_response(spec) for spec in build_tool_registry().specs_for_permissions(permissions)]


@router.post("/tools/{tool_name}/execute", response_model=ToolExecuteResponse)
def execute_tool(
    tool_name: str,
    body: ToolExecuteRequest,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.ORGANIZATION_READ)),
) -> ToolExecuteResponse:
    registry = build_tool_registry()
    context = _tool_context(principal, request)
    try:
        execution = registry.execute(
            tool_name,
            body.arguments,
            context,
            confirmed=body.confirmed,
        )
    except ToolNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ToolPermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ToolConfirmationRequiredError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return ToolExecuteResponse(
        tool_name=execution.tool_name,
        correlation_id=execution.correlation_id,
        output=execution.output,
    )
