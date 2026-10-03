# OferBus Phase C.5 — Result recalculation and revision comparison v0.1

Status: IMPLEMENTED / CI PENDING

## Purpose

Phase C.5 makes the validity boundary of planning results explicit after manual plan editing. A result is valid only for the exact immutable `PlanRevision` for which its `ResultSnapshot` was persisted.

## Result freshness contract

`GET /plans/{plan_revision_id}/result-status` returns one of two states:

- `fresh`: a `ResultSnapshot` exists for that exact revision;
- `needs-recalculation`: no snapshot exists for that exact revision.

When a manual child has no exact snapshot, a parent's result is explicitly reported as `stale`. Parent metrics are never silently copied or presented as child metrics.

This is deliberately fail-closed. The current characterized computation pipeline produces computed plan revisions from scenario inputs; it has not yet been promoted as a semantics-preserving recalculation engine for arbitrary manually edited plan revisions. C.5 therefore exposes `needs-recalculation` rather than inventing a recomputation path.

## Parent → child comparison

`GET /plans/{plan_revision_id}/compare-parent` compares the persisted operational state of a child with its direct parent. It reports changed trips and changed vehicle-block summaries using stable sequence/block numbers and named changed fields. A root revision returns conflict because it has no parent.

The comparison is structural and semantic-layer preserving. It does not claim that stale dependent metrics have been recomputed.

## Invariants

- Computed and parent revisions remain immutable.
- Tenant/RBAC boundaries use `result:read`.
- `legacy-exact`, `normalized`, and `modern` remain explicit on the plan revision and comparison response.
- No SQL is generated or executed by AI; API code uses the persistence layer/SQLAlchemy.
- No result is considered fresh merely because its parent has a result.
- Actual recomputation for edited plans remains gated until its model semantics are characterized and promoted.

## Acceptance

C.5 is CONCLUDED only after the exact final commit is integrated into the GitHub default branch and the canonical Python, Web, and integrated PostgreSQL/API/worker/rendered-web CI gates are green.
