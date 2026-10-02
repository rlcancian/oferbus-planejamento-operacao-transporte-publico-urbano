# OferBus Core

This directory is reserved for the production computational engine.

`reference-core/` remains the executable archaeological/characterization source of truth until individual models are deliberately promoted. Promotion requires explicit semantics, deterministic tests, known units, provenance and a decision about historical defects.

The production core will expose the three accepted semantic families:

- `legacy-exact` — reproduced historical behavior;
- `normalized` — recovered OferBus semantics with confirmed implementation defects corrected;
- `modern` — new scientific/operational models.

Phase A.1 intentionally contains no copied implementation here. Blindly moving the current reference package would blur the boundary between characterization evidence and production code.
