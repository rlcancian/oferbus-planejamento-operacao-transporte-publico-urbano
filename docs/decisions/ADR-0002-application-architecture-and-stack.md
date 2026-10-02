# ADR-0002 — OferBus application architecture and stack

- **Status:** Accepted for initial materialization
- **Date:** 2026-10-02

## Context

The reconstructed OferBus contains a deterministic/scientific planning core, long-running optimization workloads, an interactive March Diagram, multi-tenant B2B requirements and PostgreSQL-oriented immutable scenario/result provenance.

The new system must modernize the product without coupling scientific algorithms to the browser, rewriting them in a presentation language, or prematurely fragmenting the backend into microservices.

## Decision

The initial OferBus 2026 architecture is:

- **Web:** Next.js 16 + React 19.2 + TypeScript 5.x;
- **API/application backend:** Python + FastAPI;
- **computational engine:** independent versioned Python package;
- **database:** PostgreSQL 18;
- **database access/migrations:** SQLAlchemy 2.1 + Alembic + psycopg 3;
- **long-running jobs:** Celery 5.x stable + Redis;
- **API contract:** OpenAPI, with generated TypeScript client/types;
- **March Diagram:** custom interactive renderer, initially SVG + D3 utilities;
- **testing:** pytest, Vitest/React Testing Library and Playwright;
- **CI:** GitHub Actions;
- **deployment unit:** containers;
- **architecture style:** modular monolith with separate web/API/worker processes, not microservices.

PostgreSQL is the source of truth. Redis is not authoritative storage.

The computational engine supports three semantic families:

- `legacy-exact`;
- `normalized`;
- `modern`.

## Rationale

Python preserves continuity with the executable reconstruction work and is appropriate for deterministic algorithms, optimization and future scientific tooling. FastAPI provides a thin application/API boundary around that engine rather than embedding domain algorithms in HTTP handlers.

Next.js/React/TypeScript provides the browser platform needed for rich planning workflows and a highly interactive March Diagram without requiring the computational core to be ported to JavaScript.

PostgreSQL matches the already accepted persistence model and provides strong transactional integrity, relational constraints and tenant-isolation mechanisms.

Celery/Redis keeps expensive planning/optimization workloads outside request lifetimes while allowing the same Python computational package to run in API tests and workers.

A modular monolith minimizes operational and distributed-systems complexity while preserving clear domain boundaries. Modules can be split later only when actual scale/isolation requirements justify it.

## Deferred decisions

This ADR does not select:

- the final OIDC identity provider;
- cloud/vendor;
- Kubernetes;
- PostGIS activation;
- final PDF/reporting engine;
- Canvas/WebGL renderer;
- AI model/provider;
- billing/payment stack.

## Consequences

The next implementation step should bootstrap a monorepo with `apps/web`, `apps/api`, `apps/worker`, a promoted `packages/oferbus-core`, physical PostgreSQL migrations and CI, then implement one complete planning vertical slice before broad CRUD or advanced UI work.
