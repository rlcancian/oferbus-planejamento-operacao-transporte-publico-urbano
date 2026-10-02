# OferBus — Phase A.4 Asynchronous Computation Boundary v0.1

**Status:** concluded baseline  
**Date:** 2026-10-02

## Purpose

Establish a durable asynchronous execution boundary before planning, optimization and crew workloads are connected to production handlers.

The boundary separates:

- submission and authorization in the FastAPI application;
- durable run/provenance state in `ComputationRun`;
- queue coordination in `computation_job`;
- worker process execution;
- deterministic business computation in the future `oferbus-core`.

## Queue technology

The initial queue is PostgreSQL-backed. See `docs/decisions/ADR-0004-postgresql-backed-asynchronous-computation.md`.

This minimizes operational dependencies on the initial VPS while providing durable transactional submission, concurrent consumers through `FOR UPDATE SKIP LOCKED`, leases, retries and idempotency.

The implementation lives behind the `JobQueue` protocol in `packages/oferbus-jobs`, so queue technology is replaceable without changing planning-domain APIs.

## Persistence

Migration `0003_async_computation` adds:

- status validation and indexing for `computation_run`;
- `computation_job`, one-to-one with `ComputationRun`;
- organization-aware foreign key to the run;
- submitted actor;
- JSON payload;
- progress from 0 to 100;
- queue and availability timestamps;
- claim/heartbeat/lease fields;
- attempt/max-attempt counters;
- last error;
- partial unique organization-scoped idempotency index.

## Lifecycle

```text
queued
  ↓ claim
running
  ├─ success → succeeded
  ├─ retryable error → retry_wait → running
  ├─ terminal error → failed
  └─ expired lease → reclaimed while attempts remain
```

Terminal statuses are `succeeded`, `failed` and `cancelled`.

A worker owns a run only while its lease is valid. Heartbeats extend the lease and may update progress. A run that exhausts attempts after an expired lease is failed rather than remaining permanently `running`.

## API

Authenticated organization members with `computation:run` may submit:

```text
POST /computations
```

Phase A.4 accepts only `run_kind=platform-smoke`; this restriction is deliberate until real planning handlers are connected.

Users with result-read permission may inspect:

```text
GET /computations/{run_id}
GET /computations/{run_id}/events
```

The event endpoint uses **SSE — Server-Sent Events** and emits changes in status/progress/attempt count until the run reaches a terminal state.

## Worker

`apps/worker` is now an executable Python package.

The initial `platform-smoke` handler performs only infrastructure validation: it emits progress, completes and stores diagnostics identifying its handler/worker. It does not calculate transport-planning results.

The worker bootstrap contains no planning business logic. Future handlers call the same versioned OferBus Core used by tests and application services.

## Reliability rules

- submission can carry an organization-scoped idempotency key;
- duplicate submission with the same key resolves to the existing run;
- worker claims are concurrency-safe;
- retry delay is bounded exponential backoff;
- progress must remain within 0–100;
- attempts are bounded;
- job payload is durable but is not authoritative domain state;
- durable computation outputs belong to domain/result tables, not the queue row.

## Validation status

Unit/metadata tests were added for:

- retry backoff policy;
- worker smoke lifecycle;
- tenant-aware job-to-run foreign key;
- progress/attempt invariants;
- claim and idempotency indexes.

Because this work was performed through the GitHub connector, an integrated PostgreSQL execution is intentionally deferred to Phase A.6. A.6 must actually apply migration `0003_async_computation`, seed a development scenario, submit a smoke run, execute a worker and verify terminal success.

## Exit state

Phase A.4 is complete at the architectural/code level. Phase A.5 is the next gate and introduces the provider-neutral AI/tool boundary; it does not yet connect an LLM provider.
