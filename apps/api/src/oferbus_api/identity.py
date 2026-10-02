from __future__ import annotations

import os
import uuid
from collections.abc import Callable, Generator
from enum import StrEnum
from typing import Protocol

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from oferbus_db import AppUser, Organization, OrganizationMembership, get_session_factory


class Role(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    PLANNER = "planner"
    VIEWER = "viewer"


class Permission(StrEnum):
    ORGANIZATION_READ = "organization:read"
    ORGANIZATION_ADMIN = "organization:admin"
    MEMBERSHIP_MANAGE = "membership:manage"
    PROJECT_READ = "project:read"
    PROJECT_WRITE = "project:write"
    SCENARIO_READ = "scenario:read"
    SCENARIO_WRITE = "scenario:write"
    COMPUTATION_RUN = "computation:run"
    PLAN_EDIT = "plan:edit"
    RESULT_READ = "result:read"
    AUDIT_READ = "audit:read"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.OWNER: frozenset(Permission),
    Role.ADMIN: frozenset(
        {
            Permission.ORGANIZATION_READ,
            Permission.MEMBERSHIP_MANAGE,
            Permission.PROJECT_READ,
            Permission.PROJECT_WRITE,
            Permission.SCENARIO_READ,
            Permission.SCENARIO_WRITE,
            Permission.COMPUTATION_RUN,
            Permission.PLAN_EDIT,
            Permission.RESULT_READ,
            Permission.AUDIT_READ,
        }
    ),
    Role.PLANNER: frozenset(
        {
            Permission.ORGANIZATION_READ,
            Permission.PROJECT_READ,
            Permission.PROJECT_WRITE,
            Permission.SCENARIO_READ,
            Permission.SCENARIO_WRITE,
            Permission.COMPUTATION_RUN,
            Permission.PLAN_EDIT,
            Permission.RESULT_READ,
        }
    ),
    Role.VIEWER: frozenset(
        {
            Permission.ORGANIZATION_READ,
            Permission.PROJECT_READ,
            Permission.SCENARIO_READ,
            Permission.RESULT_READ,
        }
    ),
}


class IdentityClaims(BaseModel):
    subject: str
    display_name: str | None = None
    email: str | None = None


class Principal(BaseModel):
    user_id: uuid.UUID
    organization_id: uuid.UUID
    subject: str
    display_name: str
    email: str | None = None
    role: Role

    def has_permission(self, permission: Permission) -> bool:
        return permission in ROLE_PERMISSIONS[self.role]


class IdentityContextResponse(BaseModel):
    user_id: uuid.UUID
    organization_id: uuid.UUID
    subject: str
    display_name: str
    email: str | None
    role: Role
    permissions: list[Permission]


class IdentityAdapter(Protocol):
    def authenticate(self, request: Request) -> IdentityClaims | None: ...


class DevelopmentHeaderIdentityAdapter:
    """Local-only adapter. It must never be accepted in a production environment."""

    def authenticate(self, request: Request) -> IdentityClaims | None:
        environment = os.getenv("OFERBUS_ENV", "development").lower()
        if environment in {"production", "prod"}:
            raise RuntimeError("development-header identity adapter is forbidden in production")

        subject = request.headers.get("x-oferbus-subject")
        if not subject:
            return None

        return IdentityClaims(
            subject=subject,
            display_name=request.headers.get("x-oferbus-display-name"),
            email=request.headers.get("x-oferbus-email"),
        )


class UnconfiguredIdentityAdapter:
    def authenticate(self, request: Request) -> IdentityClaims | None:
        return None


def configured_identity_adapter() -> IdentityAdapter:
    environment = os.getenv("OFERBUS_ENV", "development").lower()
    default_mode = "development-header" if environment not in {"production", "prod"} else "unconfigured"
    mode = os.getenv("OFERBUS_IDENTITY_MODE", default_mode).lower()

    if mode == "development-header":
        return DevelopmentHeaderIdentityAdapter()
    if mode == "unconfigured":
        return UnconfiguredIdentityAdapter()
    raise RuntimeError(f"Unsupported OFERBUS_IDENTITY_MODE: {mode}")


def database_session() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def parse_organization_id(request: Request) -> uuid.UUID:
    raw = request.headers.get("x-oferbus-organization-id")
    if not raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization context is required")
    try:
        return uuid.UUID(raw)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid organization context") from exc


def resolve_principal(
    request: Request,
    session: Session = Depends(database_session),
) -> Principal:
    claims = configured_identity_adapter().authenticate(request)
    if claims is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required")

    organization_id = parse_organization_id(request)
    statement = (
        select(
            AppUser.id,
            AppUser.display_name,
            AppUser.email,
            OrganizationMembership.role_key,
            OrganizationMembership.status.label("membership_status"),
            Organization.status.label("organization_status"),
        )
        .join(OrganizationMembership, OrganizationMembership.user_id == AppUser.id)
        .join(Organization, Organization.id == OrganizationMembership.organization_id)
        .where(
            AppUser.external_subject == claims.subject,
            OrganizationMembership.organization_id == organization_id,
        )
    )
    row = session.execute(statement).mappings().one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No membership in selected organization")
    if row["membership_status"] != "active" or row["organization_status"] != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization membership is not active")

    try:
        role = Role(row["role_key"])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unsupported organization role") from exc

    return Principal(
        user_id=row["id"],
        organization_id=organization_id,
        subject=claims.subject,
        display_name=row["display_name"],
        email=row["email"],
        role=role,
    )


def require_permission(permission: Permission) -> Callable[[Principal], Principal]:
    def guard(principal: Principal = Depends(resolve_principal)) -> Principal:
        if not principal.has_permission(permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing permission: {permission}")
        return principal

    return guard


router = APIRouter(prefix="/identity", tags=["identity"])


@router.get("/me", response_model=IdentityContextResponse)
def current_identity(principal: Principal = Depends(resolve_principal)) -> IdentityContextResponse:
    return IdentityContextResponse(
        user_id=principal.user_id,
        organization_id=principal.organization_id,
        subject=principal.subject,
        display_name=principal.display_name,
        email=principal.email,
        role=principal.role,
        permissions=sorted(ROLE_PERMISSIONS[principal.role], key=str),
    )
