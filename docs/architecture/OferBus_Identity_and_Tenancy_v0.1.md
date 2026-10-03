# OferBus — Identity and Tenancy Boundary v0.1

**Status:** Phase A.3 baseline  
**Date:** 2026-10-02

## Purpose

Separate four concerns that must remain independent in a multi-organization B2B system:

1. external authentication;
2. application user identity;
3. active organization (tenant) context;
4. authorization permissions.

## Request resolution

```text
external credentials
→ IdentityAdapter
→ external subject
→ app_user
→ explicit organization selection
→ organization_membership
→ Principal(user, organization, role)
→ permission guard
→ domain use case
→ audit event in same transaction for mutations
```

The LLM/Copilot introduced later must pass through the same permission/domain-command boundary. It does not receive a privileged bypass.

## Development adapter

Phase A.3 provides `development-header` exclusively for local development.

Headers:

- `X-OferBus-Subject` — external development subject;
- `X-OferBus-Organization-ID` — selected organization UUID;
- `X-OferBus-Display-Name` — optional informational claim;
- `X-OferBus-Email` — optional informational claim.

The authoritative name/email used by the resolved principal come from `app_user`; external claims are authentication inputs, not implicit profile writes.

`development-header` is rejected when `OFERBUS_ENV=production` or `prod`.

## Initial roles

| Role | Intent |
| --- | --- |
| `owner` | organization owner and highest application authority |
| `admin` | manages members and operational configuration |
| `planner` | develops projects/scenarios and executes planning |
| `viewer` | read-only project/scenario/result access |

Authorization is permission-based. The current capability vocabulary includes organization read/admin, membership management, project read/write, scenario read/write, computation execution, plan editing, result reading and audit reading.

## Persistence

Phase A.2 already introduced `app_user` and `organization_membership`. Migration `0002_identity_tenancy` adds:

- validated role/status values at database level;
- `audit_event`;
- organization/time and actor/time audit indexes.

The audit event snapshots the external subject and role in addition to the application user ID. This preserves meaningful history even if memberships change later.

## Row-Level Security

RLS is deliberately deferred until the database has separate migration-owner and application-runtime roles. Cross-tenant foreign keys and application guards are active now; RLS is a later defense-in-depth layer and must be tested under the actual runtime role before production.

## Provider integration contract

A future OIDC adapter is responsible only for validating provider credentials and returning stable claims such as `subject`, optional display name and optional email. It must not decide project permissions or tenant membership.

This keeps provider choice replaceable and allows municipality/operator SSO variants without changing planning-domain rules.

## Phase A.3 exit conditions

- provider-neutral identity adapter exists;
- development adapter cannot operate in production;
- organization context is explicit;
- active membership is required;
- RBAC permissions are centralized and tested;
- `/identity/me` exposes resolved context;
- audit identity propagation exists;
- RLS decision is documented with prerequisites for activation.
