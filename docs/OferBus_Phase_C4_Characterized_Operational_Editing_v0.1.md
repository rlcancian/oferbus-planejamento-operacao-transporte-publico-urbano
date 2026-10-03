# OferBus Phase C.4 — Characterized Operational Editing v0.1

Status: IMPLEMENTED, AWAITING FINAL CI GATE

## Scope

C.4 extends the immutable revision editing boundary only where semantics are already explicit in the persisted model. The new typed command is `set-trip-express`, which changes `PlannedTrip.is_express` in a newly derived manual `PlanRevision`. Parent revisions remain immutable; command journal, author, reason, correlation id, tenant/RBAC boundary and audit event remain mandatory.

## Characterization gate

The persisted model distinguishes the boolean operational property `is_express` independently from `trip_type`. This boolean can therefore be edited without inventing a legacy mapping or a new operational rule.

The following candidate C.4 operations remain deliberately unsupported and fail closed at request validation:

- `create-trip`: creation semantics affect direction numbering, timing, service level, block ordering and downstream results and are not yet sufficiently characterized.
- `remove-trip`: removal semantics affect block topology and downstream indicators and are not yet sufficiently characterized.
- `set-trip-type`: the admissible taxonomy and its legacy/normalized/modern mappings are not yet sufficiently characterized.
- `assign-trip-block`: insertion/reordering/deadhead/layover semantics are not yet sufficiently characterized.

Absence of these commands is intentional domain protection, not an implementation omission. They may be promoted only after archaeological/domain evidence defines their invariants and validation rules.

## Command

`POST /plans/{plan_revision_id}/edits`

```json
{
  "client_command_id": "uuid",
  "command_type": "set-trip-express",
  "reason": "operational reason",
  "trip_sequence_no": 2,
  "is_express": true
}
```

The command clones the parent revision, changes only the selected child's `is_express`, persists previous/new values in `PlanEditCommand.payload`, records `plan.trip.express-status-set`, and commits atomically. Replaying the same `client_command_id` returns the same derived revision.

## Acceptance

C.4 is CONCLUDED only when the exact final commit passes Python quality/tests, PostgreSQL/API/worker integrated acceptance, and web typecheck/build. Until then its status is IMPLEMENTED/AWAITING CI.
