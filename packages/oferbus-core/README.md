# OferBus Core

`oferbus-core` is the production computational boundary of OferBus 2026.

Phase B.1 materializes the first stable planning contracts while preserving the separation from `reference-core/`, which remains archaeological/characterization evidence.

## Current production boundary

The package now defines:

- typed planning input/output contracts with explicit operational units;
- semantic layers `legacy-exact`, `normalized` and `modern`;
- deterministic canonical SHA-256 input/output fingerprints;
- validation for service windows, observations, curves, capacity, vehicle and cost inputs;
- `ReferencePlanningAdapter`, an explicitly temporary bridge over characterized routines;
- no PostgreSQL, FastAPI, worker or UI dependency.

The reference bridge currently exercises the characterized chain:

```text
minimum timetable
→ operational trip attributes
→ basic link graph
→ effective fleet / vehicle blocks
→ service level
→ occupancy
→ operating/cost metrics
```

For `legacy-exact`, characterized historical behavior is retained where the reference harness supports it. For `normalized`, the bridge currently applies the characterized corrections for return passenger replay, express-trip occupancy semantics and direction-weighted distance metrics.

`modern` deliberately raises `NotImplementedError` until a real modern planning model is promoted. The system must not advertise a computational capability that does not exist.

## Important limitation

The bridge is not a declaration that `reference-core` itself is production code. The basic graph still excludes unpromoted `Cria_1`, `Cria_2`, garage-check and fine-adjustment stages. Individual algorithms will be deliberately promoted behind these stable contracts during Phase B.

## Testing

From the repository root after `make bootstrap`:

```bash
make test-python
```

The Phase B.1 tests include deterministic fingerprint checks and parity against the existing single-direction end-to-end reference fixture.
