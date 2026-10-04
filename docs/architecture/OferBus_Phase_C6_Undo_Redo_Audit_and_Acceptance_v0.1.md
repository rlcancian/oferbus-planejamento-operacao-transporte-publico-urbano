# OferBus — Phase C.6 Undo/Redo, Audit and Acceptance v0.1

**Status:** EM ANDAMENTO  
**Date:** 2026-10-04

## Factual checkpoint

Phase C.5 is complete on the canonical default branch. C.6 is the active subphase.

This checkpoint materializes the first C.6 safeguards without declaring the subphase complete.

## Revision navigation

Undo/redo is non-destructive. `GET /plans/{plan_revision_id}/history` returns:

- the explicit ancestor chain for undo navigation;
- explicit child revisions as redo candidates;
- command type, reason and author where the revision was produced by a persisted edit command.

No historical `PlanRevision` is mutated. A branch point may have multiple redo candidates; the API exposes them explicitly rather than guessing which branch the planner intended.

## Persistence correction discovered during C.6

Inspection found a real schema/model mismatch: the API had already promoted typed `move-trip` and `set-trip-express` commands, while the PostgreSQL check constraint and ORM metadata still admitted only `fork`.

Migration `0007_plan_edit_command_types` and the ORM constraint now admit exactly the characterized command set:

- `fork`;
- `move-trip`;
- `set-trip-express`.

No uncharacterized generic patch or legacy link-building command is admitted.

## Density gate

`scripts/march_density_benchmark.mjs` compares deterministic SVG serialization cost with Canvas command-preparation cost at 250, 1000 and 5000 trips. CI fails if the 1000-trip SVG serialization median exceeds 100 ms.

The Canvas number is deliberately a command-preparation signal, not a browser rasterization/FPS claim. A browser-level benchmark remains necessary before any rendering-technology migration decision.

## Remaining before C.6 can be concluded

- expert keyboard workflow on the rendered March surface;
- cross-selection among timetable, vehicle blocks and March Diagram;
- browser interaction coverage for critical edit/history flows;
- conflict/warning rendered acceptance;
- browser-level SVG/Canvas density evidence or an explicit documented limitation of the synthetic gate;
- final integrated CI PASS on the canonical default branch;
- canonical Phase C plan/status update.

C.6 must remain **EM ANDAMENTO** until these items are integrated and validated.
