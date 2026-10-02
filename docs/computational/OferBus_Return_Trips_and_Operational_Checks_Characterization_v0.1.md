# OferBus — Return Trips and Operational Checks Characterization v0.1

Date: 2026-10-02

## Scope

This document characterizes the legacy routines related to automatic return-trip creation and operational consistency checks in `MMARCHA1.BAS`.

Acronyms used here:

- **BC — Bug Candidate**: a candidate defect found in the legacy source, preserved or isolated rather than silently corrected.
- **IR — Índice de Renovação**: demand-renewal index used elsewhere in the planning model; mentioned only for consistency with the computational catalog.

## `Cria_2`

`Cria_2` tries to repair an unresolved vehicle chain by inserting an opposite-direction return trip between:

1. a trip whose destination has no outgoing link; and
2. a later same-direction trip whose origin has no incoming link.

The active 2008 source has separate branches according to the presence of storage at the terminal.

### Storage-enabled branch

The source searches a later same-direction target and opposite-direction trips that delimit a feasible insertion interval. Two start cases are source-confirmed:

- if a backward opposite-direction anchor exists, its departure defines the beginning of the interval;
- otherwise the interval begins one minute after the current trip's virtual arrival.

The reference core covers both cases when the forward anchor exists. The inserted trip is type `2` for a normal created return or type `3` for an express/deadhead created return.

Link result:

- current trip exit -> direct trip;
- inserted trip entry -> direct trip;
- inserted trip exit -> storage;
- target trip entry -> storage.

### No-storage branch

The active 2008 source adds a substantially more complex branch not present in the older preserved `__MMARCHA1.BAS` implementation.

The reference core now implements the fully anchored subcase where all three source anchors exist:

- previous opposite-direction trip before the target;
- next opposite-direction trip at/after the target;
- previous same-direction departure before the target.

The code then places the return inside the recovered interval and rewrites storage/direct links according to the source's conflict check.

### BC-012 — unsafe/unreliable no-storage fallbacks

Two fallback paths are not yet executed by the reference core:

- the backward search starts at `m = k`, decrements `m`, but tests `m <= gNumObjViagem` rather than a lower bound such as `m >= 1`; if the assumed previous trip does not exist, the loop can scan before the beginning of the array;
- one fallback computes the arrival limit with `Calc_ChegadaVirtual(Sent, ...)` while the new trip being created is in `outroSent`.

These are source facts. Whether they were reachable in valid historical projects is still unknown. They are therefore classified as **BC-012**, not automatically corrected.

## `Verifica_Ida_Garagem`

The routine removes a created express/deadhead trip (`Tipo = 3`) when it has no exit link. Before deletion it searches backward for an opposite-direction predecessor and clears that predecessor's exit link.

This confirms a useful domain rule: an express/deadhead trip that no longer connects the vehicle to a useful subsequent operation should not remain in the schedule merely because it was previously generated.

### BC-011 — skip after deletion

After deleting trip `i`, the VB routine increments `i`. The next array element is shifted into the deleted position and can therefore escape inspection. The reference core provides both:

- `legacy-exact`: preserve the increment/skip;
- normalized: recheck the shifted element.

The defect matters only when consecutive removable express trips can occur. Historical reachability is not yet proven.

## `Verifica_Intervalo_4Min`

The routine counts consecutive same-direction departures whose real departure interval is strictly below four minutes.

Important semantics:

- the global trip array is assumed to be ordered by virtual time;
- the measured interval uses real departure time;
- radial directions are tracked independently;
- express/deadhead trips are not excluded;
- exactly four minutes is not counted; only intervals `< 4` are counted.

The count is used both for a user warning after planning and in the explanatory text associated with projected effective fleet.

## Executable status

Implemented and tested:

- `Cria_2`, storage branch with and without backward anchor, when the forward anchor exists;
- `Cria_2`, fully anchored no-storage branch;
- orphan express/deadhead removal;
- legacy and normalized post-delete behavior;
- interval-under-four-minutes counting;
- previous `Cria_1`, linking, fleet allocation, fine adjustment, occupancy and result metrics remain integrated.

Not yet claimed as executable parity:

- `Cria_2` fallbacks that depend on BC-012 paths;
- numerical identity against a historical executable binary.

## Validation

```text
python -m pytest -q
52 passed

python -m compileall -q src tests
PASS
```
