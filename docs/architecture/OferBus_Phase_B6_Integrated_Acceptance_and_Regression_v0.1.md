# OferBus — Phase B.6 Integrated Acceptance and Regression Gate v0.1

**Status:** CONCLUÍDA  
**Date:** 2026-10-02

## Objective

Close Phase B with an automated acceptance path proving the complete first operational planning slice from deterministic input through the rendered web workspace.

## Accepted path

The CI gate now proves, in one PostgreSQL-backed job:

```text
migrations
→ deterministic seed
→ FastAPI + worker
→ immutable ScenarioRevision input
→ core-planning submission
→ deterministic worker execution
→ PlanRevision / PlannedTrip / VehicleBlock / ResultSnapshot persistence
→ exact API reconstruction and fingerprint verification
→ Next.js production build/start
→ rendered planning workspace acceptance
```

The rendered workspace acceptance requires the production Next.js server to expose the real persisted fixture and verifies stable operational semantics rather than CSS/pixel details:

- scenario `Phase B Core Planning Fixture`;
- line `DEV-001 · Linha de Desenvolvimento OferBus`;
- computed-plan state;
- normalized semantic layer;
- planned timetable;
- vehicle blocks;
- verified fingerprint provenance;
- absence of empty/error workspace states.

The acceptance script is `scripts/web_acceptance.py`.

## Repeatable integration smoke

`scripts/integration_smoke.py` is intentionally repeatable against an already-used development database. Each invocation uses a fresh idempotency key for smoke computations so a previously completed `ComputationRun` cannot masquerade as a newly queued run.

Stable context assertions use deterministic entity identifiers for project/scenario/revision identity. Display names are not treated as immutable database identity because older development databases may preserve historical seed labels.

## Golden master regression

`packages/oferbus-core/tests/test_reference_bridge.py` pins the normalized Phase B fixture to a characterized golden master:

- input fingerprint: `98add8a4013c8104444b8a93c629869a2c5304b9f598b14cf3e2621e72b95974`;
- output fingerprint: `eda24324f17235703f6c004e7fc60c338b16059828a896fb11a9e1e447e6bd48`;
- trips: `7`;
- effective fleet: `2`;
- passengers: `61`;
- total distance: `56 km`;
- daily cost: `112`;
- distance semantics: `direction-weighted`.

A deliberate scientific/model change may update this golden master only together with an explicit explanation of the semantic change and its provenance.

## Quality gates

Phase B completion requires all of the following in the same repository state:

- Python dependency consistency, syntax, lint, tests and dependency audit;
- OferBus Core golden-master regression;
- strict TypeScript typecheck;
- Next.js production build;
- npm runtime dependency audit;
- PostgreSQL 18 migrations and deterministic seed;
- API and worker startup;
- real `core-planning` execution;
- relational result persistence and exact fingerprint reconstruction;
- `GET /results/computations/{run_id}` and `GET /results/latest` acceptance;
- Next.js production-server startup;
- rendered planning workspace acceptance.

## Local acceptance

Phase B was also exercised on the development notebook with PostgreSQL 18 on the local OferBus container, `make dev`, repeatable `make smoke`, and browser inspection of the real planning workspace.

## Phase B conclusion

Phase B is complete. OferBus now has a truthful vertical slice in which a deterministic, immutable planning input can be computed asynchronously, persisted with provenance, reconstructed by fingerprint and inspected in the browser.

The next architecture phase is Phase C, centered on the March Diagram and versioned operational editing. Phase C must preserve the immutable computed `PlanRevision` as the parent of any manually edited derivative revision rather than mutating historical results in place.
