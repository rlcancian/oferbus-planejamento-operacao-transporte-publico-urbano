# ADR-0004 — PostgreSQL-backed asynchronous computation

- **Status:** Accepted for Phase A baseline
- **Date:** 2026-10-02

## Context

OferBus planning, optimization, multiline processing, reporting and future crew scheduling may exceed normal HTTP request lifetimes. The platform therefore needs durable asynchronous jobs, progress reporting, retries, idempotent submission and safe execution by multiple worker processes.

The initial product will run on the same deployment VPS as other systems and PostgreSQL is already mandatory. Introducing Redis/Celery immediately would add another authoritative operational dependency before actual workload measurements exist.

## Decision

The Phase A queue is PostgreSQL-backed.

`ComputationRun` remains the authoritative domain/provenance record. A 1:1 `computation_job` record stores execution-coordination state:

- submitted user;
- idempotency key;
- serialized job payload;
- progress percentage;
- queued/available/claimed/heartbeat timestamps;
- lease owner and expiration;
- attempt count and maximum attempts;
- last execution error.

Workers claim eligible records with PostgreSQL row locking using `FOR UPDATE SKIP LOCKED`. A lease/heartbeat mechanism permits recovery after worker failure. Expired jobs may be reclaimed while attempts remain; exhausted jobs become failed.

Retry delay uses a bounded exponential backoff. Submission may carry an organization-scoped idempotency key enforced by a partial unique index.

API and worker depend on a `JobQueue` abstraction implemented initially by `PostgresComputationQueue`. Queue-specific SQL and lifecycle logic do not belong in HTTP endpoints or planning algorithms.

Progress is exposed by normal run-status queries and by **Server-Sent Events (SSE)** for browser updates. SSE is sufficient because Phase A progress flow is server-to-client; WebSockets remain deferred until a genuinely bidirectional realtime requirement exists.

## Initial handler

Phase A.4 registers only `platform-smoke`. It verifies the infrastructure chain:

`API → PostgreSQL → worker claim → heartbeat/progress → terminal result`.

It is not a transport-planning algorithm. Production planning handlers will later invoke the versioned OferBus Core.

## Why not Celery + Redis now?

PostgreSQL provides the features required for the initial expected workload:

- durable transactional submission;
- row-level locking;
- concurrent consumers with `SKIP LOCKED`;
- indexes and retry scheduling;
- no additional broker service on the initial VPS.

This is an operational simplification, not a permanent prohibition on brokers.

## Reconsideration triggers

Re-evaluate Celery/Redis, another broker, or separate queue infrastructure if measurements show one or more of:

- sustained queue throughput creating material PostgreSQL contention;
- large numbers of independent worker pools/routing keys;
- advanced scheduling/rate-control requirements not justified to implement in the PostgreSQL queue;
- queue isolation requirements that should not share database resources with transactional workloads;
- horizontal deployment at a scale where broker-specific operational tooling materially improves reliability.

Because `JobQueue` is an abstraction, changing the queue implementation must not change planning-domain contracts.

## Consequences

The platform now requires a worker process in addition to web/API/PostgreSQL for asynchronous runs to progress. If no worker is running, queued runs remain durable and visible rather than being lost.

A.6 must include an integrated local test that applies migration `0003_async_computation`, seeds a valid scenario revision, submits `platform-smoke`, runs a worker and verifies terminal completion.
