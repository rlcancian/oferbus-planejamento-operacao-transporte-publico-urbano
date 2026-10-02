# OferBus worker

This directory is the process boundary for long-running Python computations.

## Queue foundation

The initial durable queue is **PostgreSQL-backed**. `ComputationRun` remains the authoritative execution/provenance record and `computation_job` stores coordination metadata: queue availability, progress, lease ownership, heartbeat, retry count and idempotency key.

Workers claim jobs with PostgreSQL row locking using `FOR UPDATE SKIP LOCKED`, so multiple worker processes can compete safely without executing the same leased job concurrently.

The queue contract lives in `packages/oferbus-jobs`; API and worker depend on that abstraction rather than embedding queue SQL in application endpoints.

## Handlers

### `platform-smoke`

Infrastructure-only regression handler retained from Phase A. It validates:

`API → PostgreSQL queue → worker → heartbeat/progress → completion`.

It is not a planning algorithm.

### `core-planning`

Phase B.3 introduces the first real deterministic planning handler:

```text
ComputationRun
→ load immutable ScenarioRevision planning snapshot
→ verify tenant + persisted fingerprint
→ verify queued semantic layer and engine version
→ execute ReferencePlanningAdapter / oferbus-core contract
→ verify engine input fingerprint/provenance
→ persist output fingerprint + technical diagnostics
→ mark run succeeded
```

The worker does **not** accept ad-hoc scientific parameters in the job payload. All planning inputs come from the immutable scenario revision created by the application boundary.

The handler reports progress at meaningful boundaries (load/verify, compute, finalize). Deterministic input/model errors are terminal and non-retryable; unexpected infrastructure errors remain eligible for bounded queue retries.

Detailed timetable, vehicle-block and metrics persistence is intentionally deferred to Phase B.4. B.3 stores only execution provenance, fingerprints and a compact diagnostic summary in `ComputationRun`.

## Reproducibility guardrails

- semantic layer is derived from the immutable scenario snapshot, not trusted from a client payload;
- queued input fingerprint must equal the snapshot fingerprint at worker execution time;
- queued engine descriptor must equal the worker engine descriptor;
- returned engine provenance and input fingerprint are checked before success;
- output fingerprint is written to `ComputationRun` on successful planning;
- reuse of an idempotency key for materially different computation metadata is rejected.

## Why not Celery + Redis yet?

The initial deployment is expected to share the existing VPS and PostgreSQL is already mandatory. A PostgreSQL queue minimizes services and gives transactional/idempotent submission. The `JobQueue` abstraction preserves the option to move to Celery/Redis or another broker if measured throughput, scheduling or isolation requirements justify it.
