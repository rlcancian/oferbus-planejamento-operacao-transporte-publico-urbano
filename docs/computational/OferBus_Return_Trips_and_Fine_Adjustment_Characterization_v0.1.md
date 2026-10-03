# OferBus — Return Trips and Fine Adjustment Characterization v0.1

Date: 2026-10-02

## Scope

This document characterizes two late stages of the march-diagram construction pipeline:

- `Cria_2`, which creates additional return trips when an unresolved vehicle chain can be made feasible by inserting an opposite-direction movement;
- `Verifica_Ajuste_1`, the automatic one-minute fine-adjustment pass.

## Cria_2

**CONFIRMED IN CODE**

`Cria_2` scans trips whose destination/output link is still unresolved. For a radial line it evaluates whether a later trip in the same direction, also lacking an input link, can be reached if an opposite-direction return trip is inserted between them.

The source computes a feasible insertion interval using existing opposite-direction trips, storage-area behavior, real/virtual departure times and the travel-time model. It may create a normal return (`Tipo=2`) or an express/deadhead return (`Tipo=3`) depending on project configuration.

### Reconstructed executable branch

The reference core currently implements the storage-enabled branch for which both temporal anchors are explicitly found by the source. In this branch:

1. current trip output becomes `TRIP`;
2. inserted return input becomes `TRIP`;
3. inserted return output becomes `STORAGE`;
4. target trip input becomes `STORAGE`;
5. a normal return departure is chosen near the midpoint of the recovered feasible virtual-time interval and converted back to a real departure.

The remaining unanchored/no-storage branches contain additional source quirks and remain `PARTIAL`; they are not guessed.

## Fine adjustment

**CONFIRMED IN CODE**

`Verifica_Ajuste_1` searches for exact virtual-time coincidence between an arrival and a departure in the compatible direction. When allowed by the link guards, the departing trip is moved by one virtual minute via `Desloca_Viagem`.

For a normal trip, the real departure is incremented until the requested virtual departure shift is reached. For an express trip, real departure is moved directly by one minute. `Preenche_Atributos_Viagem` then recalculates arrival/virtual times and resets links, vehicle and crew assignments before relinking.

## BC-007 — Bug Candidate 007

The 2008c source contains:

```text
valorI = gObjViagem(i).Vinculos
valorJ = gObjViagem(i).Vinculos
```

The second assignment is strongly expected to read trip `j`. As written, the guard for the candidate trip input link is evaluated against trip `i` instead.

The executable reference exposes both variants:

- `preserve_bc007_link_variable_bug=True`: exact source behavior;
- `False`: candidate-link guard uses trip `j`.

A characterization fixture demonstrates a case where the source behavior blocks a valid one-minute adjustment while the corrected variant performs it.

## BC-006 — Bug Candidate 006

In both major construction/reconstruction flows the source calls `Cria_2`, then immediately assigns `vinculo = 0`, and only afterwards tests `If vinculo > 0 Then ...` to decide whether to rebuild direct/storage links. This makes that relinking block unreachable regardless of the result returned by `Cria_2`.

This remains a source-level defect candidate. The reference core does not reproduce the unreachable control-flow wrapper; it reconstructs the algorithmic stage independently.

## Status

- `Cria_1`: executable characterization available;
- `Cria_2`: storage-enabled anchored branch executable; remaining branches partial;
- one-minute fine adjustment: executable;
- BC-006: source defect characterized;
- BC-007: legacy and corrected variants executable;
- full march-diagram orchestration with all return-trip branches: not yet complete.
