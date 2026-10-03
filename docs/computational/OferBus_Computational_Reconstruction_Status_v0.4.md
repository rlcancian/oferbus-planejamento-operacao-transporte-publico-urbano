# OferBus — Computational Reconstruction Status v0.4

Date: 2026-10-02

## Delta from v0.3

This increment closes the current TPV/IR/MPTDC characterization gate.

New executable evidence:

- TPV initial-missing extrapolation characterized;
- TPV final `2` versus sentinel `-2` defect characterized in both legacy and corrected modes;
- variable IR lower bound (`IR >= 1`) characterized;
- constant IR branch characterized through the common adjustment stage;
- MPTDC period values verified as means of the original demand curve;
- MPTDC 30-minute crossing-boundary suppression characterized.

A new source-level candidate defect, **BC-009**, was identified in radial MPTDC processing: shared `Faixa()` state and a `Maxi` tied to the active global direction can contaminate one direction with another. The reference core remains normalized per direction and records the anomaly instead of reproducing it silently.

## Verification

```text
python -m pytest -q
....................................
36 passed

python -m compileall -q src tests
PASS
```

## Current gate

| Area | Status |
|---|---|
| Demand reconstruction | PASS |
| TPV | PASS characterized; legacy/corrected terminal-sentinel variants explicit |
| IR | PASS characterized |
| MPTDC | PASS per-direction; Manual-2005 / Code-2008c variants explicit; radial shared-state anomaly recorded |
| Forecast >=3 complete years | PASS |
| Minimum timetable 2007 | PASS structural for characterized branches |
| Complete trip attributes | PASS structural |
| Direct/storage/garage links | PASS structural |
| Vehicle allocation / effective fleet | PASS structural |
| Service level | PASS structural |
| `Cria_1` | PASS initial reconstruction |
| `Cria_2` | ANALYZED, not yet executable |
| Fine adjustment | ANALYZED, not yet executable |
| Metrics/costs | NEXT |
| Historical executable identity | UNKNOWN |

## Next unit

Reconstruct projected occupancy and result/cost indicators formula-by-formula, keeping every metric tied to its legacy source procedure and units.
