# OferBus — Phase A Platform Skeleton Plan v0.1

**Status:** implementation complete; workstation acceptance pending  
**Date:** 2026-10-02

## Goal

Establish the minimum production-shaped repository skeleton for OferBus 2026 without prematurely implementing business modules.

## Phase A.1 — skeleton — CONCLUÍDA

Materialized: root workspace metadata, Next.js/React web shell, FastAPI `/health`, worker boundary placeholder, `oferbus-core` promotion boundary and environment placeholders.

## Phase A.2 — persistence baseline — CONCLUÍDA

Materialized: optional PostgreSQL 18 local service, `packages/oferbus-db` with SQLAlchemy/psycopg, Alembic `0001_foundation`, foundational organization/project/scenario/computation schema, tenant-aware composite keys, invariant tests, API `/ready` and web readiness status.

The remaining accepted logical tables are intentionally materialized together with the vertical slices that exercise them rather than frozen in one oversized initial migration.

## Phase A.3 — identity and tenancy boundary — CONCLUÍDA

Materialized: provider-neutral `IdentityAdapter`, local-only development identity adapter, explicit active-organization context, application `Principal`, centralized RBAC permission matrix (`owner`, `admin`, `planner`, `viewer`), `/identity/me`, audit identity propagation, `audit_event` persistence and migration `0002_identity_tenancy`.

PostgreSQL Row-Level Security (RLS) was evaluated and is deliberately deferred until migration-owner and application-runtime database roles are separated. Composite tenant foreign keys and application authorization remain the active controls in the current development baseline.

## Phase A.4 — asynchronous computation boundary — CONCLUÍDA

Materialized:

- PostgreSQL-backed durable queue selected for the initial deployment;
- migration `0003_async_computation` and `computation_job` execution metadata;
- `packages/oferbus-jobs` with a backend-neutral `JobQueue` contract and `PostgresComputationQueue` implementation;
- organization-scoped idempotency key;
- `FOR UPDATE SKIP LOCKED` concurrent claiming;
- worker lease, heartbeat and crash recovery semantics;
- bounded exponential retry policy and attempt limits;
- Python worker process in `apps/worker`;
- API submission/status endpoints under `/computations`;
- Server-Sent Events (SSE) progress stream;
- `platform-smoke` infrastructure handler only, explicitly not a planning algorithm;
- unit/metadata tests for retry policy, worker lifecycle and queue invariants.

Celery/Redis is not required for the initial VPS deployment. ADR-0004 defines measurable triggers for revisiting a dedicated broker while preserving the `JobQueue` contract.

## Phase A.5 — AI and tool boundary skeleton — CONCLUÍDA

Materialized:

- `packages/oferbus-ai` with provider-neutral `LLMProvider` request/response/tool-call contracts;
- explicit `UnconfiguredLLMProvider` baseline — no vendor is silently selected;
- structured `ToolRegistry` with allow-listed tools only;
- permission-aware tool discovery and execution using the authenticated user's organization and role;
- risk classes (`read`, `compute`, `mutate`, `admin`) and explicit confirmation policy;
- conservative baseline: computation/mutation/admin actions require confirmation;
- operational audit through the existing `audit_event` model without automatically storing full argument payloads;
- API `/ai/status`, `/ai/tools` and `/ai/tools/{tool_name}/execute`;
- first truthful tool catalog: platform description, computation status and confirmed `platform-smoke` submission;
- direct SQL access by the LLM structurally excluded;
- ADR-0005 documenting provider neutrality, authorization, confirmations, audit and deterministic computation boundaries;
- unit tests for authorization, confirmation, unknown-tool rejection and unconfigured-provider status.

No planning-domain AI tool is advertised until the corresponding deterministic domain command exists. Provider integration, conversational orchestration and RAG are intentionally later concerns built on this boundary.

## Phase A.6 — quality gate and local startup — IMPLEMENTADA; ACEITAÇÃO LOCAL PENDENTE

Materialized:

- `.github/workflows/ci.yml` with independent Python, web and integrated PostgreSQL smoke jobs;
- fatal-error Python lint gate, compile validation, test suites and dependency audit;
- TypeScript typecheck, Next.js production build and npm runtime dependency audit;
- deterministic `scripts/dev_seed.py` fixture for organization/user/project/scenario/revision;
- `scripts/integration_smoke.py` exercising API → identity → AI tool → `ComputationRun` → PostgreSQL queue → worker → success;
- `scripts/dev-bootstrap.sh` for Python/Node dependency bootstrap;
- `scripts/dev-run.sh` for API + worker + web local execution;
- `scripts/dev-doctor.sh` for workstation diagnostics;
- root `Makefile` with `bootstrap`, `postgres-up`, `migrate`, `seed`, `doctor`, `dev`, `smoke` and quality commands;
- `OferBus_Phase_A6_Quality_Gate_and_Local_Startup_v0.1.md` runbook covering Docker and native PostgreSQL paths.

GitHub Actions runs were successfully triggered for the Phase A.6 commits. A green workflow is required for remote CI acceptance; the development-workstation run remains required to validate the actual Ubuntu environment, local PostgreSQL configuration and browser startup.

## Exit criteria for Phase A

Repository implementation for A.1–A.6 is complete. Phase A acceptance is complete only after the development workstation verifies:

- PostgreSQL is reachable and Alembic reaches `0003_async_computation`;
- deterministic seed succeeds;
- `make doctor` passes;
- API and worker share the durable run state;
- `make smoke` reaches `succeeded` with 100% progress through the AI tool boundary;
- the Next.js OferBus shell opens in the browser;
- local Python tests/typecheck/build are either passing or any environment-specific failure is diagnosed and corrected.

No planning-domain completeness is required until Phase B.
