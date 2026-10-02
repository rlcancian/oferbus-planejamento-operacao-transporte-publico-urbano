# OferBus — Computational Reconstruction Status v0.6

Date: 2026-10-02

## Delta from v0.5

This increment advances three areas:

1. correct domain semantics for express/deadhead trips in projected occupancy;
2. executable reconstruction of the anchored storage-enabled branch of `Cria_2`;
3. executable reconstruction of the one-minute fine-adjustment pass and an end-to-end reference fixture.

## Acronyms used in this checkpoint

- **IR — Índice de Renovação**.
- **BC — Bug Candidate**, a candidate defect found in the legacy source and not silently corrected.

## Express-trip occupancy semantics

Domain clarification: a legacy OferBus express trip is an operational/deadhead movement and transports zero passengers.

Two normalized indicators are now distinct:

- **projected mean occupancy rate**: express trips carry zero passengers but remain in the denominator;
- **projected mean operational occupancy rate**: express trips are excluded and only passenger-service trips are averaged.

The legacy-exact 2008c implementation remains separately available because it assigns a passenger-demand interval to express trips. This narrower inconsistency is now BC-010.

## Cria_2

The anchored storage-enabled branch is executable and tested. It reconstructs the insertion interval, creates the opposite-direction return and rewrites the three relevant links.

Status remains **PARTIAL** because the unanchored/no-storage branches are not yet sufficiently characterized to claim complete reconstruction.

## Fine adjustment

`Verifica_Ajuste_1` + `Desloca_Viagem(..., 1)` are executable.

BC-007 is now demonstrated by test: the 2008c typo reads both link variables from trip `i`; the corrected variant reads the candidate input link from trip `j` and can perform an otherwise blocked one-minute adjustment.

BC-006 remains a source-level control-flow candidate defect: after `Cria_2`, the caller resets `vinculo` to zero before testing it, preventing the intended relinking block from executing.

## End-to-end reference fixture

A deterministic in-memory fixture now validates the chain:

`demand`
→ `minimum timetable`
→ `complete trip attributes`
→ `trip links`
→ `vehicle allocation / fleet`
→ `service level`
→ `normalized projected occupancy`
→ `operating indicators`
→ `cost`

This is the first executable test that crosses all of those layers in one run. It is a synthetic characterization fixture, not yet a historical golden master.

## Verification

```text
python -m pytest -q
...............................................
47 passed

python -m compileall -q src tests
PASS
```

## Current gate

| Area | Status |
|---|---|
| Demand reconstruction | PASS |
| Travel-time profile | PASS with legacy/corrected sentinel variants |
| IR — Índice de Renovação | PASS structural |
| Typical constant-demand periods | PASS structural with Manual-2005 / Code-2008c variants |
| Forecasting | PASS for characterized historical models |
| Minimum timetable 2007 | PASS structural for characterized branches |
| Complete trip attributes | PASS structural |
| Direct/storage/garage links | PASS structural |
| Vehicle allocation / effective fleet | PASS structural |
| Per-trip service level | PASS structural |
| Occupancy/results/costs | PASS structural with legacy/normalized variants |
| Cria_1 | PASS structural for characterized behavior |
| Cria_2 | PARTIAL — anchored storage branch executable |
| Fine adjustment | PASS structural with BC-007 variants |
| End-to-end synthetic reference fixture | PASS |
| Historical golden-master identity | UNKNOWN |
| Crew scheduling | PARTIAL archaeology |

## Next gate

1. complete the remaining `Cria_2` branches and characterize BC-006 around relinking;
2. reconstruct the remaining graph/march-diagram cleanup behavior such as `Verifica_Ida_Garagem` and interval diagnostics;
3. then freeze the first modern scenario/result data contract suitable for PostgreSQL, preserving algorithm version, semantic layer (`legacy-exact` versus `normalized`) and provenance.
