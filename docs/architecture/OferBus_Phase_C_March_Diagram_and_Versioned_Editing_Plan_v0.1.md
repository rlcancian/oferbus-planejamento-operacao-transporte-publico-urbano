# OferBus — Phase C March Diagram and Versioned Operational Editing Plan v0.1

**Status:** EM ANDAMENTO  
**Date:** 2026-10-02

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

## C.1 — March read model and read-only SVG surface — EM ANDAMENTO

Materialize a dedicated tenant-safe read model for March Diagram rendering and the first precise browser visualization.

Scope:

- plan revision identity, parent/source metadata and semantic layer;
- exact service-time domain;
- line/direction/terminal context;
- actual and virtual trip times;
- normal/express semantics;
- vehicle block identity;
- SVG time axis and terminal rails;
- trip trajectories with block and direction information;
- accessible inspection/tooltips;
- responsive rendering without changing operational coordinates;
- rendered-web CI acceptance.

C.1 is deliberately read-only. No drag operation may mutate data until the command/versioning boundary exists.

## C.2 — Versioned editing domain and persistence boundary — PENDENTE

Introduce the explicit manual-revision command model and persistence required for derived plans.

Expected scope:

- manual revision author/reason metadata;
- edit-operation journal with typed command payloads;
- transactional clone/materialization from parent revision;
- monotonic revision numbering under concurrency;
- tenant-safe parent lineage validation;
- audit events for edit commands;
- API commands returning a new revision rather than mutating the parent.

## C.3 — Time editing and operational conflict validation — PENDENTE

Implement the first mutation visible in the March Diagram: moving a trip in service time.

Expected scope:

- change departure time command;
- preserve travel-time relationship unless an explicit command changes it;
- immediate validation for ordering, overlap and block feasibility;
- preview/confirmation boundary;
- derived `PlanRevision` creation;
- UI selection, keyboard adjustment and drag interaction mapped to the same command.

## C.4 — Trip and block/link editing — PENDENTE

Promote the remaining central March Diagram operations:

- create trip;
- remove trip;
- change trip type / express semantics;
- move trip between vehicle blocks;
- change block ordering / operational links;
- expose effects on effective fleet and incompatible chains.

Any legacy link-building behavior must be promoted only after characterization. C.4 must not invent unverified `Cria_1` / `Cria_2` semantics.

## C.5 — Dependent result recalculation and comparison — PENDENTE

After a manual plan edit, recompute the dependent result snapshot without replacing the edited plan.

Expected scope:

- occupancy/service-level recomputation where inputs remain valid;
- fleet/block indicators;
- distance and cost metrics;
- new `ResultSnapshot` lineage associated with the manual plan;
- before/after comparison against the parent plan;
- explicit stale/needs-recalculation states when a dependent model is not yet promoted.

## C.6 — Undo/redo, audit, acceptance and density gate — PENDENTE

Close Phase C with production-grade editing safeguards:

- undo/redo implemented as revision navigation/derived commands, not destructive history mutation;
- complete audit trail and authorship;
- keyboard workflow for expert planners;
- cross-selection between timetable, blocks and March Diagram;
- conflict/warning acceptance tests;
- browser interaction tests for critical commands;
- SVG/Canvas density benchmark using realistic trip volumes;
- rendered regression gate for read and edit flows.

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
