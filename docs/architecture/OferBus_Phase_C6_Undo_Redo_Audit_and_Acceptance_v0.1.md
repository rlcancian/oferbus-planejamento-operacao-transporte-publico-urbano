# OferBus — Phase C.6 Undo/Redo, Audit and Acceptance v0.1

**Status:** EM ANDAMENTO  
**Date:** 2026-10-04

## Factual checkpoint

Phase C.5 is complete on the canonical default branch. C.6 is the active subphase.

The interaction checkpoint at `d233882de16cab064e2c46f7365aea0fc94cd236` is integrated on `master` and OferBus CI run `37184019306` completed successfully. This validates the current Python, Web/build/density and integrated acceptance gates for that exact checkpoint; it does **not** imply that the remaining C.6 interaction requirements are complete.

## Revision navigation

Undo/redo is non-destructive. `GET /plans/{plan_revision_id}/history` returns the explicit ancestor chain for undo navigation and explicit child revisions as redo candidates, including persisted command type, reason and author where available. No historical `PlanRevision` is mutated. Branch points expose all redo candidates rather than guessing planner intent.

## Persistence correction discovered during C.6

Migration `0007_plan_edit_command_types` and ORM metadata admit exactly the characterized command set: `fork`, `move-trip`, and `set-trip-express`. No uncharacterized generic patch or legacy link-building command is admitted.

## Interaction checkpoint

The March SVG now exposes each trip trajectory as a keyboard-focusable interaction target with an accessible trip description and Enter/Space activation contract. Focus and selected-state styling are explicit, and the rendered acceptance contract has been advanced from the obsolete C.1 read-only marker to the C.6 interaction surface.

Repository inspection confirms that `MarchDiagram` already accepts controlled `selectedTripSequence` / `onSelectTrip`, but `PlanningWorkspace` still renders it as `<MarchDiagram plan={march} />` and timetable/block surfaces have no shared selection owner. Therefore cross-selection is **not yet complete**; the next coherent implementation step is to make the workspace a client-side selection owner and propagate the selected trip to all three surfaces. Browser-level event automation also remains pending.

## Density gate

`scripts/march_density_benchmark.mjs` compares deterministic SVG serialization cost with Canvas command-preparation cost at 250, 1000 and 5000 trips. CI fails if the 1000-trip SVG serialization median exceeds 100 ms. This is not a browser rasterization/FPS claim; browser-level evidence remains necessary before a rendering-technology migration decision.

## Remaining before C.6 can be concluded

- shared selected-trip state and cross-selection among timetable, vehicle blocks and March Diagram;
- expert workspace keyboard navigation beyond per-trip Enter/Space activation;
- browser interaction coverage for critical edit/history flows;
- conflict/warning rendered acceptance;
- browser-level SVG/Canvas density evidence or an explicit documented limitation of the synthetic gate;
- final integrated CI PASS on the canonical default branch;
- canonical Phase C plan/status update.

C.6 must remain **EM ANDAMENTO** until these items are integrated and validated.
