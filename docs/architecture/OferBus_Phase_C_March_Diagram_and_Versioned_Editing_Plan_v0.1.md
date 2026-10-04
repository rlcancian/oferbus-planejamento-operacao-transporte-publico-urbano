# OferBus — Phase C March Diagram and Versioned Operational Editing Plan v0.1

**Status:** EM ANDAMENTO — C.1–C.5 concluídas; C.6 em andamento  
**Date:** 2026-10-04

## Goal

Recover the March Diagram as a first-class operational engineering surface in the modern OferBus while preserving immutable computed history.

The governing lineage is:

```text
computed PlanRevision
→ read-only March Diagram
→ validated edit command
→ derived manual PlanRevision
→ updated trips / blocks
→ recomputed dependent indicators
→ auditable provenance
```

A manual operation must never mutate a historical computed plan in place.

## Invariants

- `PlanRevision` is immutable after materialization.
- Every manual revision has an explicit `parent_plan_revision_id`.
- Editing is command-based and tenant/RBAC guarded; the browser does not write SQL-shaped data.
- Service times remain integer service minutes.
- Every trip remains uniquely identifiable inside its plan revision.
- Direction, trip type, express semantics and vehicle block are never inferred only from visual color.
- Invalid operational states are rejected or explicitly represented as warnings according to named validation rules.
- Recalculation must never silently overwrite a manual decision.
- Authorship, reason and edit provenance must be persisted for manual revisions.
- The March Diagram is an engineering editor; visual design may improve usability but cannot change operational meaning.

## C.1 — March read model and read-only SVG surface — CONCLUÍDA

Materialized:

- API `0.10.0` with tenant-safe `GET /plans/{plan_revision_id}/march`;
- plan revision identity, parent/source metadata, semantic layer and output fingerprint in the March read model;
- exact service-time domain derived from persisted real and virtual trip times;
- line, direction and origin/destination terminal context;
- actual/virtual trip times, normal/express semantics, vehicle block and service level;
- explicit rejection of ambiguous direction keys instead of drawing a potentially incorrect multi-line plan;
- semantic SVG March Diagram in the operational workspace;
- horizontal service-time axis with explicit clock labels;
- terminal rails and trip trajectories using domain coordinates rather than decorative placement;
- separate dashed virtual trajectory when virtual and actual times differ;
- vehicle-block visual distinction plus sequence number, direction and native SVG tooltip so meaning does not depend only on color;
- responsive horizontal overflow and reduced-motion-safe hover emphasis;
- dedicated error state for the March surface without taking down the rest of the planning workspace;
- integrated smoke assertions for plan, terminal, time-domain and trip semantics;
- rendered Next.js production acceptance requiring the real March Diagram and rejecting the fallback/error surface.

The current persisted trip contract identifies directions by `direction_key`. C.1 therefore rejects a scenario where the same key is ambiguous across multiple lines. A later multi-line promotion must persist an explicit line/direction identifier on planned trips rather than infer it in the UI.

## C.2 — Versioned editing domain and persistence boundary — CONCLUÍDA

Materialized and integrated on the default branch:

- explicit manual revision author/reason metadata;
- typed edit-operation journal;
- transactional parent-to-child revision materialization;
- monotonic revision numbering and tenant-safe lineage validation;
- audit events for edit commands;
- command API returning derived revisions instead of mutating historical plans.

## C.3 — Time editing and operational conflict validation — CONCLUÍDA

Materialized and integrated:

- typed `move-trip` command over integer service minutes;
- preservation of trip duration unless explicitly changed by another characterized operation;
- operational conflict validation and explicit conflict reporting;
- derived immutable `PlanRevision` creation through the same command/versioning boundary.

## C.4 — Trip and block/link editing — CONCLUÍDA NO ESCOPO CARACTERIZADO

Materialized and integrated only where semantics are sufficiently characterized:

- typed express/type editing and vehicle-block reassignment boundaries;
- persistence support for the promoted command types;
- no invented `Cria_1` / `Cria_2` legacy link semantics.

Creation/removal or link-building behavior whose legacy meaning remains uncharacterized is intentionally not fabricated and remains outside the promoted semantic surface.

## C.5 — Dependent result recalculation and comparison — CONCLUÍDA

Materialized and integrated:

- explicit dependent-result recalculation boundary;
- parent→child comparison;
- stale/needs-recalculation representation where a dependent model is not promoted;
- result lineage associated with immutable plan revisions;
- final default-branch CI checkpoint `aa82bfa50c9117c56dfcb90546fe4a799d0befa8` passed all OferBus CI gates.

## C.6 — Undo/redo, audit, acceptance and density gate — EM ANDAMENTO

Integrated checkpoints so far:

- history API exposes ancestors for undo and explicit direct-child redo candidates without destructive history mutation;
- audit/authorship remain attached to the revision/command lineage;
- command persistence accepts the promoted `fork`, `move-trip` and `set-trip-express` command types;
- March trajectories are keyboard-focusable and selectable with pointer, `Enter` and `Space`;
- `PlanningWorkspace` owns `selectedTripSequence` and propagates it across March Diagram, timetable and vehicle-block markers;
- selecting the same trip again clears the shared selection;
- deterministic SVG/Canvas preparation benchmark runs in CI at 250, 1,000 and 5,000 trips, with a 100 ms gate at 1,000 trips;
- the synthetic benchmark is not treated as evidence of browser rasterization/FPS and therefore does not by itself justify a Canvas migration;
- default-branch checkpoint `45a9d1d27eb0968db69d3163fba98753be0a0269` passed OferBus CI run `37189812329`.

Still required before C.6 can be declared complete:

- browser-level interaction tests for the critical selection/edit/history workflows;
- rendered acceptance of conflict/warning states rather than only the nominal workspace;
- browser-level density evidence for the March surface, or an explicit, evidence-backed limitation if the CI environment cannot supply a reproducible browser benchmark;
- final integrated default-branch CI PASS after those gates are materialized.

## Visualization technology decision

C.1 uses semantic SVG as the default because current OferBus trip volumes and interaction requirements benefit from:

- exact vector geometry;
- accessible DOM elements;
- native event targeting;
- straightforward time-axis scaling;
- deterministic browser tests;
- future vector/PDF export.

D3 is not required for the initial implementation; scale/tick logic remains small and explicit. Canvas remains an optimization option only if C.6 density benchmarks justify it. WebGL is not justified for the 2D March Diagram.

## Phase C exit criteria

Phase C is complete when a planner can inspect a real persisted plan in the March Diagram, select and modify operational trips/links through validated commands, obtain derived immutable plan revisions, inspect dependent effects, navigate edit history, and reproduce/audit the complete lineage without ever mutating the original computed plan.
