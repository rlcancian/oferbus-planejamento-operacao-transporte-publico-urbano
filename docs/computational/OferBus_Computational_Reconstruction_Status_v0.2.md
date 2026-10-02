# OferBus — Computational Reconstruction Status v0.2

Date: 2026-10-02

## Current gate

| Area | Status | Evidence |
|---|---|---|
| Passenger/minute reconstruction | PASS | executable + tests |
| Original demand curve | PASS | executable + tests |
| Legacy smoothing/adjustment | PASS | executable + tests |
| Demand total correction | PASS | executable + tests |
| Robust maximum | PASS | executable + tests |
| Capacity/service-level curve | PASS with candidate defect versioned | executable + tests |
| Forecast regressions | PASS for >=3 complete-year branch | executable + tests |
| Virtual departure/arrival | PASS | executable + tests |
| TPV original/interpolated | PASS with sentinel divergence versioned | executable + tests |
| Renewal index | PASS structural | executable + tests |
| MPTDC | PASS structural; 2005/2008 divergence versioned | executable + tests |
| Minimum timetable 2007 | PASS structural for characterized branches | executable + tests |
| Return-trip replay anomaly | VERSIONED; full adversarial fixture pending | code + switchable implementation |
| `Ajeitadinha` | ANALYZED, not yet ported | source reviewed |
| Complete planned-trip attributes | ANALYZED, not yet ported | source reviewed |
| Trip/storage/garage linking | NEXT | source pipeline located |
| Vehicle blocks/fleet allocation | ANALYZED, reconstruction next | source reviewed |
| Crew scheduling | PARTIAL archaeology only | not in current tranche |
| Historical executable golden master | UNKNOWN | no execution of legacy binary |

## Test evidence

`python -m pytest -q` → **15 passed**.

## Architectural consequence

Historical file formats are no longer an architectural target. They may be retained only
as archaeological evidence or one-time migration input. The modern persistence model will
be PostgreSQL-based and derived from the reconstructed domain and computational contracts.

## Immediate next gate

A scenario should become able to execute, entirely in memory:

`adjusted curves`
→ `minimum timetable`
→ `complete planned trips`
→ `operational links`
→ `vehicle blocks`
→ `fleet size`
→ `service-level indicators`.

Success requires deterministic tests for the resulting graph, not merely successful code
execution.
