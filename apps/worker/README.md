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

The deterministic planning handler executes:

```text
ComputationRun
→ load immutable ScenarioRevision planning snapshot
→ verify tenant + persisted fingerprint
→ verify queued semantic layer and engine version
→ execute ReferencePlanningAdapter / oferbus-core contract
→ verify engine input/output fingerprints and provenance
→ persist PlanRevision / PlannedTrip / VehicleBlock / ResultSnapshot
→ reconstruct persisted PlanningResult and verify fingerprint
→ mark run succeeded
```

The worker does **not** accept ad-hoc scientific parameters in the job payload. All planning inputs come from the immutable scenario revision created by the application boundary.

The handler reports progress at meaningful boundaries (load/verify, compute, persist/finalize). Deterministic input/model/result-integrity errors are terminal and non-retryable; unexpected infrastructure errors remain eligible for bounded queue retries.

## Result persistence and crash recovery

`core-planning` persists the complete operational result before marking the queue run as `succeeded`. The persistence boundary is idempotent by `computation_run_id`.

If the database commit succeeds and the worker fails before `queue.succeed(...)`, a retry does not create a second plan. It reloads the existing immutable `PlanRevision`, verifies semantic layer, engine provenance and fingerprints, reconstructs the result, and continues only if the material result is identical.

## Reproducibility guardrails

- semantic layer is derived from the immutable scenario snapshot, not trusted from a client payload;
- queued input fingerprint must equal the snapshot fingerprint at worker execution time;
- queued engine descriptor must equal the worker engine descriptor;
- returned engine provenance and input fingerprint are checked before persistence;
- persisted result is reconstructed and must reproduce the exact output fingerprint;
- output fingerprint is written to `ComputationRun` only on successful planning completion;
- reuse of an idempotency key for materially different computation metadata is rejected.

## Why not Celery + Redis yet?

The initial deployment is expected to share the existing VPS and PostgreSQL is already mandatory. A PostgreSQL queue minimizes services and gives transactional/idempotent submission. The `JobQueue` abstraction preserves the option to move to Celery/Redis or another broker if measured throughput, scheduling or isolation requirements justify it.
