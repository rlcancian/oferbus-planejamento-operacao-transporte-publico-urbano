# OferBus Phase C.2 — Versioned Editing Boundary v0.1

Status: **IMPLEMENTED — pending exact-commit CI validation**

## Objective

Establish the transactional boundary for manual plan editing without yet introducing a semantic trip mutation. A computed `PlanRevision` remains immutable. Editing begins by producing a manual child revision whose full trip/block graph is cloned from its parent and whose provenance is journaled.

## Contract

`POST /plans/{plan_revision_id}/edits` accepts only the typed `fork` command in C.2. The request requires a caller-generated `client_command_id` and a non-empty reason. Arbitrary JSON patching is deliberately rejected; temporal and structural commands belong to C.3/C.4 after their validation semantics exist.

The operation is tenant-scoped and requires `plan:edit`. It allocates the next scenario revision number while locking the scenario revision row, creates `source_kind=manual`, sets `parent_plan_revision_id`, clears `computation_run_id`, clones planned trips, vehicle blocks and block-trip links, writes an immutable `PlanEditCommand`, writes an `AuditEvent`, and commits all of those changes atomically.

`client_command_id` is unique per organization. A repeated request returns the already-created child rather than creating a second revision. This is the idempotency boundary for UI/network retries.

## Persistence

Migration `0006_plan_editing` introduces `plan_edit_command` plus revision-level authorship/reason columns reserved for the evolving editing model. The command journal stores actor (`created_by`), reason, parent, derived revision, command type, payload and timestamp. Tenant-aware foreign keys prevent cross-organization parent/child references.

C.2 intentionally does **not** create a new `ResultSnapshot`: the fork has unchanged plan content but no independent recomputation. C.5 will define derived-result freshness/recalculation semantics rather than silently copying computed metrics as if they had been recomputed.

## Invariants

- computed revisions are never updated;
- every manual edit starts from an explicit parent and produces a new revision;
- service times remain integer minutes;
- semantic layer and engine provenance are inherited, never inferred;
- PostgreSQL is the source of truth;
- command + child graph + audit event share one transaction;
- unsupported edit types fail at request validation.

## Acceptance gate

C.2 is complete only when the exact final commit passes Python lint/tests/audit, migration application against PostgreSQL, integrated API/worker smoke, TypeScript typecheck and Next.js production build. The next phase is C.3: typed temporal edits and conflict validation, operating on this immutable revision boundary.
