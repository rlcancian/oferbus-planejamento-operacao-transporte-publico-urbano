# ADR-0003 — Identity, tenancy and authorization boundary

- **Status:** Accepted for Phase A.3
- **Date:** 2026-10-02

## Context

OferBus 2026 is a multi-organization B2B platform. A person may legitimately belong to more than one organization (for example a municipality, operator or consultancy), so authentication identity and active tenant context cannot be conflated.

The final OpenID Connect (OIDC) provider is intentionally not selected yet. Application authorization must remain independent of that provider.

## Decision

### Authentication

The API exposes a replaceable `IdentityAdapter` boundary. Provider-specific credentials are converted into stable external identity claims. The domain never depends directly on an Auth0, Keycloak, Supabase, Microsoft Entra, Google or other provider SDK.

For local development only, `development-header` accepts explicit `X-OferBus-*` headers. The adapter raises an error if used while `OFERBUS_ENV` is `production`/`prod`.

### Tenant selection

Every authenticated domain request must carry an explicit active organization context. The current development contract uses `X-OferBus-Organization-ID`; a future browser session may carry the same selection through a server-side session/token mechanism.

The API resolves the external identity to `app_user`, verifies an active `organization_membership`, verifies the selected organization is active, and only then creates a `Principal`.

### Authorization

Initial RBAC (Role-Based Access Control) roles:

- `owner` — complete organization-level authority;
- `admin` — membership and operational administration, excluding owner-only organization authority;
- `planner` — create/edit projects and scenarios, run computations and edit plans;
- `viewer` — read projects, scenarios and results without mutation rights.

Endpoints authorize against named permissions such as `project:write`, `scenario:write`, `computation:run` and `plan:edit`, rather than scattering role-name comparisons through handlers.

### Audit identity propagation

`audit_event` persists organization, application user, external subject snapshot, role snapshot, event/entity information, optional correlation ID and structured details. Mutation and its audit event are intended to share the same database transaction.

### PostgreSQL Row-Level Security

RLS (Row-Level Security) was evaluated as defense in depth and is **not activated in Phase A.3**.

Reason: effective RLS requires the application runtime to connect using a non-owner database role and to establish tenant context per transaction (`SET LOCAL` or equivalent). The current development database uses one bootstrap owner role for migrations and application access. Enabling policies under that arrangement would either provide misleading protection or complicate migrations without actually establishing the desired privilege boundary.

Before production deployment, the database operational model must split at least:

1. migration/owner role;
2. application runtime role;
3. optional read/reporting roles.

At that point tenant context can be transaction-scoped and RLS policies added without changing domain APIs.

## Consequences

- identity provider can be replaced without changing the OferBus domain;
- tenant choice is explicit and auditable;
- authorization rules are testable independently of HTTP handlers;
- local development remains possible before a real OIDC provider is selected;
- development headers are never an acceptable production authentication mechanism;
- composite tenant foreign keys from Phase A.2 remain the first database-level cross-tenant protection;
- RLS remains a production-hardening gate, not a falsely enabled checkbox.
