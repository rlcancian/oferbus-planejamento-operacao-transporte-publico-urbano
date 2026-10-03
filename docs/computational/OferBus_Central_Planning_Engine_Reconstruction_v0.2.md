# OferBus — Central Planning Engine Reconstruction v0.2

Date: 2026-10-02

## 1. Scope

This document records the second computational-reconstruction tranche. The objective is
not to redesign the scheduling method, but to make the historical planning semantics
explicit, executable and testable before any production architecture is selected.

Primary legacy evidence:

- `MPROCEDI.BAS::Realiza_Ajuste_De_Curvas`
- `MPROCEDI.BAS::Ajusta_Uma_Curva`
- `MPROCEDI.BAS::Calcula_Passageiros_Por_Minuto`
- `MPROCEDI.BAS::Calcula_Curva_Original`
- `MPROCEDI.BAS::Calcula_Org_Tmp`
- `MGERAL.BAS::Calcula_Periodos_Tipicos`
- `MFUNCOES.BAS::Calc_SaidaVirtual`
- `MFUNCOES.BAS::Calc_ChegadaVirtual`
- `MMARCHA1.BAS::Calcula_Quadro_Horarios_Minimo_2007`
- `MPROCEDI.BAS::Make_Urban_Line_Project`

## 2. Recovered execution chain

The source-confirmed central chain is:

`observed trips`
→ passenger/minute reconstruction
→ original demand curve
→ adjusted demand curve
→ demand-total correction
→ optional MPTDC transformation
→ original/adjusted IR
→ original/adjusted TPV
→ optional demand forecast scaling
→ robust demand maximum
→ virtual-time parameterization
→ minimum timetable
→ trip attribute completion
→ march-diagram linking
→ fleet allocation
→ service-level calculation.

The first ten stages are now represented directly in the reference core; the minimum
timetable itself has also been reconstructed in executable form.

## 3. TPV reconstruction

### Evidence status

`CONFIRMED IN CODE`.

`Calcula_Org_Tmp` compacts valid travel-time observations and linearly interpolates
between their departure times. Missing observations are represented internally using
sentinels `-1` and `-2`.

### Candidate defect retained as a variant

At the final boundary the 2008c source tests:

`If Flag(Qui) = 2 Then`

while the sentinel introduced by the same procedure is `-2`.

Consequently the reference core exposes two explicit behaviors:

- `preserve_sentinel_bug=True`: exact recovered 2008c branch;
- `False`: candidate corrected behavior using `-2`.

No correction is silently substituted for legacy behavior.

## 4. Renewal-index reconstruction

### Constant mode

When `CodIndiceRenova = 0`, the IR curve is constant at the line-level configured value.

### Variable mode

When a variable IR is used, the code:

1. reconstructs passengers/minute using `NumPassCritico`;
2. builds an original critical-section passenger curve;
3. computes `IR(t) = demand(t) / critical_section_passengers(t)`;
4. substitutes `1` when the denominator is zero;
5. clamps values below 1 to 1;
6. computes an arithmetic mean IR;
7. applies the same generic curve-adjustment routine used elsewhere.

This branch is now executable and tested.

## 5. MPTDC version split

The divergence previously identified is now encoded rather than merely documented.

### `code-2008c`

- intermediate demand adjustment forced to level 2;
- number of horizontal bands = `AjustePeriodo * 2`;
- band limits truncated to two decimal places;
- boundaries occur on strict crossings of a band;
- candidate periods with separation <= 30 minutes are suppressed;
- each resulting period is replaced by the mean of the *original* demand curve.

### `manual-2005`

- intermediate MDV degree 3;
- number of bands equal to the selected degree, documented as 2..9.

Both versions are kept as independently named functions. This is a model-versioning
requirement for the future production system.

## 6. Minimum timetable — recovered algorithm

`Calcula_Quadro_Horarios_Minimo_2007` is confirmed as a constructive, minute-resolution
scheduler rather than a generic optimization solver.

For each direction it:

1. anchors the process at the first observed trip when applicable;
2. scans the adjusted demand curve minute by minute;
3. accumulates passengers since the previous normal departure;
4. computes effective permitted transported demand using service-level capacity, valley
   capacity, demand intensity and IR;
5. triggers a trip when either capacity is reached or `IntervaloMax` is reached;
6. backs the trip up one minute if the last added minute would exceed the effective load;
7. at terminals without storage, watches vehicle arrivals from the opposite direction;
8. creates return trips when excess vehicles would otherwise accumulate at the terminal;
9. can mark those returns express when configured;
10. appends the final observed trip if the generated timetable ends earlier;
11. regularizes the last headways using the source's historical heuristic.

The reconstructed engine preserves the legacy trip-type codes used in this procedure:

- `0`: normal;
- `2`: normal return;
- `3`: express return.

## 7. Candidate defect: passenger replay after return trip

When a non-express return trip is created, the legacy source intends to rebuild the
passengers accumulated between the inserted return and the current scan time. However,
inside the loop it executes:

`CurvaAjustada(Sentido, cont)`

instead of indexing with the loop variable.

This was already identified archaeologically; the executable reconstruction now makes it
switchable:

- `preserve_return_replay_bug=True`: recovered source behavior;
- `False`: index by the replayed minute.

A dedicated two-direction fixture is still required before calling the corrected branch
scientifically validated.

## 8. Additional findings in the post-timetable pipeline

### 8.1 `Ajeitadinha_Brasileira_Horarios`

The source tries to move departures toward multiples of five while checking service level
and maximum headway. In the recovered 2008c procedure, the outer condition only enters
for remainders 1 or 2, making the later branch for remainders 3 or 4 unreachable. This is
`DEFECT CANDIDATE`, not yet a confirmed bug.

### 8.2 Trip attribute completion

`Preenche_Atributos_Viagem` converts the minimum timetable into complete trip objects:

- real and virtual departure;
- real and virtual arrival;
- normal versus express TPV semantics;
- resets links, vehicle and crew assignments before the linking stages.

### 8.3 March-diagram construction is a linking engine

`Constroi_Grafico_De_Marcha` is not merely a renderer. It executes operational linking:

- reorder by virtual time;
- check very short headways;
- link trips;
- link storage areas;
- radial-specific return/link adjustments;
- link garages;
- optional fine adjustment.

Therefore the future march diagram must sit on top of an explicit vehicle-link graph; it
must not own that logic solely in browser state.

### 8.4 Fleet allocation

`Ajusta_Alocacao_Da_Frota` assigns a new vehicle only to an unassigned trip and then
propagates that vehicle through compatible linked trips. The fleet size therefore emerges
from the constructed chains rather than being an independent input.

## 9. Verification

Reference-core suite after this tranche:

- previous tests: 9;
- new TPV/IR/MPTDC/timetable tests: 6;
- total: **15 PASS**.

The suite validates source-derived characterization behavior. Historical executable
identity remains `UNKNOWN` until an external historical result can be used as a golden
master.

## 10. Next reconstruction target

The next technically coherent tranche is:

1. `Preenche_Atributos_Viagem` / complete trip object;
2. `Vincula_Viagens`;
3. storage and garage link encoding;
4. `Ajusta_Alocacao_Da_Frota`;
5. service-level calculation per planned trip;
6. tests proving `timetable → links → vehicle blocks → fleet`.

Only after that chain is explicit should the production PostgreSQL schema for planned
trips, blocks and fleet plans be frozen.
