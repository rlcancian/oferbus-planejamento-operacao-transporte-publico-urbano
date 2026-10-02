# OferBus — Results, Occupancy and Costs Characterization v0.1

Date: 2026-10-02

## Scope

This document reconstructs the legacy semantics of projected occupancy, observed/projected operational indicators and line-operating costs from `MGERAL.BAS`, `MFUNCOES.BAS` and related reporting code.

## Acronyms used by the legacy code

- **IR — Índice de Renovação**: ratio between transported passengers and critical-section occupancy.
- **QDT — Quilometragem Diária Total**: total daily vehicle-kilometres used by the projected-results routine.
- **FE — Frota Efetiva**: effective number of vehicles required by the projected schedule.
- **PMD — Percurso Médio Diário**: QDT / FE.
- **OM — Ocupação Média**: transported passengers / number of trips.
- **OMTC — Ocupação Média no Trecho Crítico**: OM / mean IR.
- **IPK — Índice de Passageiros por Quilômetro**: transported passengers / QDT.
- **CDT — Custo Diário Total**.
- **CM — Custo Médio por veículo**: CDT / FE.
- **CV — Custo por Viagem**: CDT / number of trips.
- **CPP — Custo por Passageiro Equivalente**: `(CDT / passageiros) / índice de passageiros equivalentes`.
- **AM — Aproveitamento Médio**: trips / FE.
- **TMV — Tempo Médio de Viagem**.
- **VMP — Velocidade Média de Percurso**.
- **BC — Bug Candidate (defeito candidato)**: source behavior that appears inconsistent and requires characterization before correction.

## Projected-result formulas recovered

`Calcula_Inform_Resultados` computes:

- total passengers from the project demand, including forecast scaling when enabled;
- total trips from all planned trip objects;
- FE from the vehicle allocation;
- QDT as `totalTrips × arithmeticMean(extensionByDirection)`;
- PMD = QDT / FE;
- OM = passengers / trips;
- OMTC = OM / mean IR;
- IPK = passengers / QDT;
- AM = trips / FE;
- TMV = sum(realArrival - realDeparture) / trips;
- VMP = meanExtension × 60 / TMV.

Two cost models are present:

1. `TipoCusto = 0`: `CDT = QDT × costPerKm`;
2. otherwise: `CDT = QDT × variableCostPerKm + FE × typicalDayParticipation × fixedCostPerVehicle`.

Then:

- CM = CDT / FE;
- CV = CDT / trips;
- CPP = `(CDT / passengers) / equivalentPassengerIndex`.

`Calcula_Custo_Mensal` converts daily cost using `365.25 / 12 / 7` weeks/month and historical typical-day constants `4.8358`, `0.9671`, `1.1971` days/week.

## Observed baseline

`Calcula_Inform_Levantamento` differs materially from projected results: for radial lines, observed QDT is direction-weighted exactly as `trips1 × extension1 + trips2 × extension2`. It also computes TMV only from observations whose travel time is positive.

## Projected worst occupancy

`Calcula_Pior_Ocupacao_Projetada`:

1. orders planned trips by real departure;
2. accumulates demand since the previous **normal** trip in the same direction;
3. treats express trips as carrying zero passengers and does not advance the previous-normal marker;
4. divides transported passengers by IR to estimate critical-section passengers;
5. subtracts seats and divides remaining standing passengers by usable standing area to obtain density in passengers/m²;
6. records the largest transported load and the largest critical density.

## Mean projected occupancy rate

`Calcula_Taxa_Ocupacao_Projetada` follows different semantics: express trips are included, consume the demand interval, advance the previous-departure marker and remain in the averaging denominator. Capacity is `seats + 1.5 × capacityLevel × standingArea`, using the assigned vehicle model when available.

## Confirmed divergence: BC-005

**BC-005 — projected radial distance formula.**

For unequal direction lengths and unequal trip counts, projected QDT uses:

`(N1 + N2) × (L1 + L2) / 2`

while the observed baseline uses:

`N1 × L1 + N2 × L2`.

They are equal only under special conditions (for example equal trip counts or equal lengths). The reference core therefore provides both the exact legacy formula and a direction-weighted comparison variant. No silent correction is performed.

## New defect candidate: BC-010

**BC-010 — inconsistent express-trip semantics in occupancy calculations.**

The worst-occupancy routine treats express trips as zero-passenger events and leaves the demand interval for the next normal trip. The mean-occupancy-rate routine instead allocates demand to express trips and advances the interval marker. Characterization tests prove that the two rules produce different results for the same schedule.

The reference core preserves the historical mean-rate behavior in `projected_mean_occupancy_rate_legacy` and exposes a separate normalized comparison in `projected_mean_occupancy_rate_normalized`.

## Executable reconstruction

Implemented in `reference-core/src/oferbus_legacy_core/metrics.py`:

- observed baseline metrics;
- projected legacy metrics;
- direction-weighted comparison metrics;
- projected worst occupancy;
- legacy mean occupancy rate;
- normalized express-consistent occupancy rate;
- per-km and fixed+variable cost models;
- monthly-cost conversion.

## Validation

The full local reconstructed suite, synchronized with the current `main` tests plus the new metrics tests, executed successfully:

```text
44 passed
python -m compileall -q src tests
PASS
```

This is structural/behavioral characterization, not yet historical golden-master identity against an original executable run.
