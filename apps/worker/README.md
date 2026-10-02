# OferBus worker

This directory is the process boundary for long-running Python computations.

## Phase A.4 decision

The initial durable queue is **PostgreSQL-backed**. `ComputationRun` remains the authoritative domain record and `computation_job` stores execution coordination metadata: queue availability, progress, lease ownership, heartbeat, retry count and idempotency key.

Workers claim jobs with PostgreSQL row locking using `FOR UPDATE SKIP LOCKED`, so multiple worker processes can compete safely without executing the same leased job concurrently.

The queue contract lives in `packages/oferbus-jobs`; API and worker depend on that abstraction rather than embedding queue SQL in application endpoints.

## Current handler

Only `platform-smoke` is registered in Phase A.4. It exists solely to validate:

`API → PostgreSQL queue → worker → heartbeat/progress → completion`.

It is **not** a planning algorithm and must not be represented as one.

Future handlers will invoke the versioned OferBus Core. Business algorithms do not belong in this worker bootstrap.

## Why not Celery + Redis yet?

The initial deployment is expected to share the existing VPS and PostgreSQL is already mandatory. A PostgreSQL queue minimizes services and gives transactional/idempotent submission. The `JobQueue` abstraction preserves the option to move to Celery/Redis or another broker if measured throughput, scheduling or isolation requirements justify it.
