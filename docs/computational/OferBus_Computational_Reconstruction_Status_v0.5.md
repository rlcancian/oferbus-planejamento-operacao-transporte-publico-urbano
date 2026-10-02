# OferBus — Computational Reconstruction Status v0.5

Date: 2026-10-02

## Delta from v0.4

This increment reconstructs the first complete result/indicator layer above the planning and vehicle-allocation pipeline.

New executable components:

- projected worst occupancy and critical standing density;
- projected mean occupancy rate;
- observed baseline indicators;
- projected operational indicators;
- per-kilometre cost model;
- fixed + variable cost model;
- monthly cost conversion;
- explicit legacy-versus-normalized variants for known divergences.

## Acronyms

- **IR — Índice de Renovação**.
- **QDT — Quilometragem Diária Total**.
- **FE — Frota Efetiva**.
- **IPK — Índice de Passageiros por Quilômetro**.
- **BC — Bug Candidate (defeito candidato)**.

## Verification

A local mirror of the current `main` reference tests plus the new metrics tests was executed:

```text
python -m pytest -q
............................................
44 passed

python -m compileall -q src tests
PASS
```

## Defect characterization

### BC-005 — projected distance on asymmetric radial operation

The legacy projected-results routine computes QDT as total trips multiplied by arithmetic mean route length. The observed baseline computes direction-weighted distance. A fixture with unequal lengths and trip counts proves a 45 km legacy result versus 40 km direction-weighted result, with corresponding cost propagation.

Status: **CONFIRMED SOURCE DIVERGENCE; correction remains a separate variant**.

### BC-010 — express-trip treatment in mean occupancy

`Calcula_Pior_Ocupacao_Projetada` assigns zero passengers to express trips and preserves accumulated demand for the next normal trip. `Calcula_Taxa_Ocupacao_Projetada` includes express trips in demand allocation and in the averaging denominator.

Status: **CONFIRMED INTERNAL INCONSISTENCY; intended semantics still require a product/scientific decision**.

## Reconstructed metrics

The reference core now produces the source-derived equivalents of:

- total passengers;
- total trips;
- mean extension;
- total distance;
- effective fleet;
- mean daily distance per vehicle;
- mean passengers per trip;
- mean critical-section passengers per trip;
- mean occupancy rate;
- IPK;
- daily total cost;
- mean cost per vehicle;
- cost per trip;
- cost per equivalent passenger;
- mean trips per vehicle;
- mean travel time;
- mean operating speed.

## Current gate

| Area | Status |
|---|---|
| Demand / TPV / IR / MPTDC | PASS structural |
| Minimum timetable | PASS structural for characterized branches |
| Trip attributes and links | PASS structural |
| Vehicle blocks / effective fleet | PASS structural |
| Service level | PASS structural |
| Occupancy extremes | PASS structural |
| Operational result indicators | PASS structural |
| Line cost formulas | PASS structural |
| Legacy vs corrected QDT divergence | TESTED |
| Express occupancy divergence | TESTED |
| Historical executable golden-master identity | UNKNOWN |
| Crew scheduling costs | NOT YET IN THIS GATE |

## Next computational gate

The next block should complete the remaining central scheduling heuristics before database schema freeze:

1. reconstruct `Cria_2` and fine adjustment;
2. characterize BC-006 and BC-007 with executable tests;
3. build a single in-memory end-to-end fixture from demand through indicators/costs;
4. then freeze the first PostgreSQL scenario/result schema and provenance contract.
