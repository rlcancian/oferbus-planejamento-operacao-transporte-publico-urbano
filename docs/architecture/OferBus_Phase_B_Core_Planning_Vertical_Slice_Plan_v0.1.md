# OferBus — Phase B Core Planning Vertical Slice Plan v0.1

**Status:** EM ANDAMENTO  
**Date:** 2026-10-02

## Goal

Deliver the first truthful end-to-end OferBus planning workflow on top of the accepted Phase A platform foundation:

```text
line + observed trips + planning specification
→ immutable scenario revision
→ computation run
→ minimum timetable
→ operational trips / links
→ vehicle blocks / effective fleet
→ occupancy / metrics / cost
→ persisted result
→ web result workspace
```

Phase B does not attempt to port every legacy routine at once. It promotes characterized behavior in controlled increments, keeping `reference-core` as archaeological evidence and making every production contract explicit about units, semantic layer and provenance.

## B.1 — production planning contracts and reference bridge — CONCLUÍDA

Materialized:

- first installable `packages/oferbus-core` production package;
- stable typed planning input/output contracts;
- explicit service-minute, passenger, kilometre and cost units in field names/documentation;
- semantic layer selection (`legacy-exact`, `normalized`, `modern`);
- deterministic canonical SHA-256 input/output fingerprints;
- validation of direction curves, observation windows, capacities, vehicle parameters and costs;
- explicitly temporary `ReferencePlanningAdapter` executing only characterized `reference-core` routines;
- production boundary remains independent of database, HTTP, worker and UI;
- parity tests against the existing single-direction end-to-end reference fixture;
- CI and local bootstrap include `oferbus-core`.

The bridge currently exercises minimum timetable → operational trip attributes → basic link graph → vehicle blocks/effective fleet → service levels → occupancy → metrics/cost. `modern` deliberately remains unavailable rather than being faked.

For `legacy-exact`, the bridge preserves characterized historical behavior supported by the reference harness. For `normalized`, it currently applies explicit characterized corrections for return-passenger replay, express-trip occupancy semantics and direction-weighted distance metrics.

The adapter is a controlled bridge, not a declaration that the archaeological package is production code. Individual algorithms are promoted behind the same contracts in later subphases.

## B.2 — planning input persistence and application boundary — CONCLUÍDA

Materialized:

- migration `0004_planning_inputs`;
- reusable observed-trip datasets with immutable numbered revisions and content fingerprints;
- observed trips persisted per line direction;
- scenario-level planning snapshot for semantic layer, vehicle, costs and planning specification;
- per-direction snapshot for dataset revision, service window, curves, extension and storage semantics;
- shared `packages/oferbus-planning` application layer independent of FastAPI;
- creation of datasets and later immutable dataset revisions;
- creation of immutable planning `ScenarioRevision` records with canonical `PlanningInput` fingerprints;
- round-trip reconstruction that recalculates and verifies the fingerprint before returning an input;
- tenant-aware commands and composite foreign keys;
- authenticated `/planning` API endpoints;
- deterministic development fixture derived from the characterized single-direction example;
- integrated PostgreSQL/API smoke validating the persisted planning input.

Detailed design: `architecture/OferBus_Phase_B2_Planning_Input_Persistence_v0.1.md`.

## B.3 — deterministic planning worker — CONCLUÍDA

Materialized:

- `run_kind=core-planning` in the asynchronous worker;
- API submission derived from the immutable `ScenarioRevision`, not from ad-hoc scientific payloads;
- `input_fingerprint` captured at enqueue and verified again by the worker;
- semantic layer derived from the persisted snapshot and rechecked at execution;
- engine descriptor/version compatibility check between queued run and worker;
- execution through `ReferencePlanningAdapter` / `oferbus-core`;
- progress/heartbeat boundaries for load/verify, compute and finalize;
- deterministic domain/input failures marked non-retryable;
- unexpected infrastructure failures remain eligible for bounded retry;
- `output_fingerprint` persisted on successful `ComputationRun`;
- compact technical diagnostics proving trips/fleet and provenance without pretending to be final result persistence;
- strict idempotency compatibility checks for scenario, run kind, semantic layer, engine, fingerprints and payload;
- integrated PostgreSQL/API/worker smoke executing the real planning fixture end to end.

Detailed design: `architecture/OferBus_Phase_B3_Deterministic_Planning_Worker_v0.1.md`.

## B.4 — plan and result persistence — PRÓXIMA

Persist the output lineage without mutable overwrite:

```text
ScenarioRevision
→ ComputationRun
→ PlanRevision
→ planned trips / links / vehicle blocks
→ ResultSnapshot
→ metrics
```

The first schema must preserve provenance and support later March Diagram editing without freezing the full future crew/optimization model.

## B.5 — web planning result workspace — PENDENTE

Expose the first useful OferBus operational screen:

- project/scenario context;
- computation state and provenance;
- timetable table;
- vehicle/block summary;
- effective fleet;
- occupancy and core operating/cost metrics;
- semantic-layer badge and engine version;
- read-only preparation for the Phase C March Diagram.

No decorative dashboard should substitute for the operational result.

## B.6 — integrated acceptance and regression gate — PENDENTE

Add a reproducible fixture and CI/browser path proving:

```text
seed/import input
→ create scenario revision
→ submit core-planning
→ worker succeeds
→ result lineage persists
→ API returns exact result
→ web renders the result
```

Acceptance also requires regression comparison between the production contract and the characterized reference fixture for every promoted model used by the slice.

## Guardrails

- Do not silently copy known candidate defects into `normalized`.
- `legacy-exact` may preserve a defect only when explicitly characterized and named.
- Express/deadhead operational movements carry zero passengers in normalized semantics.
- Operational times are integer service minutes, not wall-clock `TIME` columns.
- The computational core must remain independent of PostgreSQL, FastAPI and React.
- AI may explain/orchestrate the workflow later, but deterministic core code remains authoritative for calculations.
- No planning-domain capability may be advertised in the Copilot before the corresponding deterministic command is implemented.

## Phase B exit criteria

Phase B is complete when a planner can create or load one line study, submit an immutable scenario revision, run deterministic planning asynchronously, inspect a persisted timetable/fleet/occupancy/metrics result in the browser, and reproduce the run from exact inputs and engine metadata.
