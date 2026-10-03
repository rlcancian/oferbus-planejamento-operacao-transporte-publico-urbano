# OferBus Phase C.3 — Temporal Editing and Conflict Validation v0.1

Status: IMPLEMENTED, awaiting exact-commit CI gate.

## Scope

C.3 promotes the C.2 versioned editing boundary from a pure `fork` to one semantic temporal command: `move-trip`. It does not mutate a `PlanRevision` in place. Every accepted command clones the parent into a new manual child and records the command/audit event in the same transaction.

## Command contract

`POST /plans/{plan_revision_id}/edits` accepts the typed command:

- `command_type = move-trip`;
- `trip_sequence_no > 0` identifies the trip inside the parent revision;
- `departure_service_minute` is a non-negative integer service minute;
- `reason` and `client_command_id` remain mandatory.

Arbitrary JSON Patch remains outside the boundary. Idempotency remains organization-scoped by `client_command_id`.

## Temporal semantics

A move changes the selected trip by one integer delta:

`delta = requested_departure - current_departure`.

The same delta is applied to actual departure, actual arrival, virtual departure and virtual arrival. Therefore actual duration, virtual duration, and the relationship between actual and virtual clocks are preserved. C.3 does not reinterpret legacy virtual-time semantics.

The computed or manual parent is never changed. The child retains `semantic_layer` (`legacy-exact`, `normalized`, or `modern`) and provenance fields inherited from the parent; result/fingerprint invalidation and dependent-metric recalculation are intentionally deferred to C.5.

## Conflict validation

After the child is cloned and the temporal delta applied, each vehicle block is validated in persisted `VehicleBlockTrip.position_no` order. For every adjacent pair:

`current.departure_service_minute >= previous.arrival_service_minute`

must hold. A violation fails closed with HTTP 409 and code `vehicle-block-time-conflict`; the transaction is rolled back, so no invalid child revision or journal entry survives. Negative actual/virtual service minutes fail with HTTP 422.

After a valid move, block boundary aggregates (`first_departure_service_minute`, `last_arrival_service_minute`, `trip_count`) are refreshed from the child trips.

This is deliberately a minimal feasibility rule. C.3 does not invent deadhead, terminal layover, relief, depot, or line-change constraints that have not yet been characterized from the legacy/domain evidence.

## Acceptance evidence

The integrated smoke creates a deterministic computed plan, moves its first trip one minute earlier, then verifies:

1. a manual child revision is created with the computed revision as parent;
2. actual and virtual timestamps all move by the same delta;
3. command replay with the same `client_command_id` returns the same child;
4. rereading the computed parent produces the same march read model as before the edit.

C.3 may be marked CONCLUDED only when Python quality/tests, PostgreSQL + API + worker integrated acceptance, and web typecheck/build all pass on the exact final commit.

## Deferred

C.4 owns trip creation/removal/type/express/block-link editing. C.5 owns result invalidation/recalculation and parent→child comparison. C.6 owns undo/redo and richer interaction acceptance.
