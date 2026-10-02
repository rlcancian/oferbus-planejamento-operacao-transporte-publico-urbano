# OferBus — Phase A Platform Skeleton Plan v0.1

**Status:** active implementation plan  
**Date:** 2026-10-02

## Goal

Establish the minimum production-shaped repository skeleton for OferBus 2026 without prematurely implementing business modules.

## Phase A.1 — skeleton — CONCLUÍDA

Materialized: root workspace metadata, Next.js/React web shell, FastAPI `/health`, worker boundary placeholder, `oferbus-core` promotion boundary and environment placeholders.

## Phase A.2 — persistence baseline — CONCLUÍDA

Materialized: optional PostgreSQL 18 local service, `packages/oferbus-db` with SQLAlchemy/psycopg, Alembic `0001_foundation`, foundational organization/project/scenario/computation schema, tenant-aware composite keys, invariant tests, API `/ready` and web readiness status.

The remaining accepted logical tables are intentionally materialized together with the vertical slices that exercise them rather than frozen in one oversized initial migration.

## Phase A.3 — identity and tenancy boundary — PENDENTE

Authentication adapter boundary, organizations/memberships/roles at application level, authorization guards, audit identity propagation, evaluate Row-Level Security, replaceable identity provider.

## Phase A.4 — asynchronous computation boundary — PENDENTE

Stable `ComputationRun` lifecycle, Python worker interface, queue selection, progress/event transport, retry/idempotency rules.

## Phase A.5 — AI and tool boundary skeleton — PENDENTE

Provider-neutral LLM adapter, structured tool contract, command authorization/confirmation policy, no direct SQL access from the LLM, audit trail for agent actions.

## Phase A.6 — quality gate and local startup — PENDENTE

CI for web/API/reference-core/persistence, lint/type checking/test commands, dependency/security checks, reproducible local startup documentation/scripts and verified browser startup workflow.

## Exit criteria for Phase A

Phase A is complete only when web, API and PostgreSQL can run together locally; migrations are reproducible; tenant isolation is testable; a computation job can be submitted through an abstraction; the AI/tool boundary exists; and CI validates the skeleton. No planning-domain completeness is required until Phase B.
