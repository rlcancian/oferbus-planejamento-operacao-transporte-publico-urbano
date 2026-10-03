# OferBus — Phase A.2 Persistence Baseline v0.1

**Status:** implemented baseline  
**Date:** 2026-10-02

## Purpose

Materialize the first physical PostgreSQL persistence layer for OferBus 2026 without freezing the entire future operational schema at once.

## Implemented scope

The baseline creates the `oferbus` PostgreSQL schema and the foundation required by the multi-user planning platform:

- organizations and application users;
- organization memberships;
- municipalities, operators and terminals;
- transit lines and explicit directions;
- planning projects and project-line associations;
- scenarios and immutable scenario revisions;
- computation-run provenance.

Operational tables for planned trips, movement connections, vehicle blocks, fleet results, curves, metrics, crew and optimization remain defined in the accepted logical persistence model and will be materialized with the vertical slices that exercise them.

## Technology

- PostgreSQL 18 baseline;
- SQLAlchemy 2.1 typed Declarative ORM;
- psycopg 3 PostgreSQL driver;
- Alembic migrations.

`packages/oferbus-db` is the authoritative Python persistence package. The Next.js application does not access PostgreSQL directly.

## Tenant invariant

Tenant-owned relationships use `organization_id` as part of composite foreign keys whenever one tenant-owned row references another tenant-owned aggregate. The database therefore rejects cross-organization references even if application authorization code is defective.

PostgreSQL Row-Level Security remains an additional defense-in-depth mechanism to be evaluated/materialized during Phase A.3.

## Revision model

The physical baseline supports `Organization → PlanningProject → Scenario → ScenarioRevision → ComputationRun`. `PlanRevision` and `ResultSnapshot` join this lineage when the first planning vertical slice is materialized.

## Migration

Initial Alembic revision: `0001_foundation`.

Migrations are the only supported mechanism for evolving a persistent OferBus database. Application startup does not call `metadata.create_all()`.

## Development PostgreSQL

`infra/dev/compose.yml` provides an optional PostgreSQL 18 container for reproducible local development. A native local PostgreSQL installation is equally supported through `DATABASE_URL`.

## Readiness

The API exposes `GET /health` for process health and `GET /ready` for PostgreSQL/migration readiness. The Next.js shell checks `/ready` server-side and visually reports whether the local persistence baseline is active.

## Validation contract

Python compilation of the persistence, migration and API modules passed in the construction environment. ORM metadata tests for tenant-aware composite keys are included. A full physical-database PASS still requires `alembic upgrade head` against PostgreSQL and will be performed in the developer environment; Docker/PostgreSQL was not available in the connector execution environment.
