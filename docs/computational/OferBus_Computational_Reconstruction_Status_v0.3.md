# OferBus — Computational Reconstruction Status v0.3

Date: 2026-10-02

## Current result

The executable reference core now reconstructs the main path from observed/adjusted demand through the first complete operational schedule representation:

`curves`
→ `minimum timetable`
→ `complete trip attributes`
→ `typed trip links`
→ `vehicle chains/blocks`
→ `effective fleet`
→ `per-trip service level`.

The reference core remains a characterization harness, not the final production architecture.

## Verification

Local reproducible validation:

```text
python -m pytest -q
............................
28 passed

python -m compileall -q src tests
PASS
```

## Newly reconstructed in v0.3

### Complete trip object

`Preenche_Atributos_Viagem` / `Preenche_Todos_Atributos_Viagens`:

- real and virtual departure;
- real and virtual arrival;
- normal versus express semantics;
- recovered express travel-time formula;
- reset of links, vehicle, driver and conductor before graph construction.

### `Tipo` bitfield

Recovered source semantics:

| Bit | Meaning |
|---:|---|
| 1 | express trip |
| 2 | trip created after the original schedule |
| 4 | departure time manually altered |
| 8 | when bit 2 is set: created by planner; otherwise: imported |
| 16 | entry link manually altered |
| 32 | exit link manually altered |

The modern reference model exposes these as named flags instead of an opaque integer.

### `Vinculos` packing

Confirmed from `Seta_Vinculo`:

- input/alpha link = `Vinculos Mod 4`;
- output/beta link = `Vinculos \\ 4`;
- `0 = none`;
- `1 = garage`;
- `2 = storage`;
- `3 = direct trip continuity`.

The modern reference representation stores entry/exit links independently and only encodes the integer for legacy characterization/migration.

### Direct linking

`Vincula_Viagens` is reconstructed. For each unresolved arrival it considers the first feasible opposite-direction departure, but refuses the link if another later same-direction arrival can claim that departure more appropriately.

### Storage and garage links

The active 2008c body of `Vincula_Estocagens` was reconstructed. Notably, the old condition checking whether the terminal actually has an `AreaEstocagem` is commented out in that procedure; the active code applies the storage-link semantics to remaining compatible pairs.

`Vincula_Garagens` then maps every remaining unresolved entry/exit to garage.

### Fleet allocation

`Ajusta_Alocacao_Da_Frota` is reconstructed. Effective fleet is not independently optimized at this stage: a new logical vehicle is created at each unassigned chain head and propagated through future trips whose temporal/directional feasibility and link codes match. Thus the fleet count emerges from the link graph.

### Service level

`Get_NivelServico`, `Calcula_Passageiros_No_Periodo`, `Acha_Viagem_Anterior`, `Calcula_NS_Viagem` and `Define_NS_Viagens` are represented in the reference core.

A historical information-loss behavior is explicit: `Get_NivelServico` may return labels such as `F1`, `F2`, ... for densities beyond F, but `Calcula_NS_Viagem` stores `Asc(label)-65`, so all such labels collapse to integer `5`.

Express trips receive `NS = -1`.

## Additional candidate defects found

### BC-006 — unreachable relinking after `Cria_2`

In both `Constroi_Grafico_De_Marcha` and `Reconstroi_Nova_Programacao`, the source executes:

```text
Cria_2 vinculo
vinculo = 0
If vinculo > 0 Then ...
```

The explicit reset makes the following relinking block unreachable regardless of what `Cria_2` reports. Classification: **strong candidate defect**.

### BC-007 — fine-adjustment link-variable typo

`Verifica_Ajuste_1` assigns both `valorI` and `valorJ` from `gObjViagem(i).Vinculos`; the second expression appears intended to use trip `j`. This can alter the guard that prevents fine adjustment across direct-trip links. Classification: **strong candidate defect**.

### BC-008 — `Cria_1` return type comment/code mismatch

For one non-express return path, `Cria_1` assigns `Tipo = 0` with comment `TODO: 2`, while other generated returns use type bit 2. This affects provenance (generated-return versus original normal trip). Classification: **confirmed source inconsistency; intended semantics not yet proven**.

## Current gate

| Area | Status |
|---|---|
| Demand reconstruction | PASS |
| TPV | PASS with legacy/corrected sentinel variants |
| IR | PASS structural |
| MPTDC | PASS structural with Manual-2005 / Code-2008c variants |
| Forecast >=3 complete years | PASS |
| Minimum timetable 2007 | PASS structural for characterized branches |
| Complete trip attributes | PASS structural |
| Trip-type provenance flags | PASS |
| Direct trip linking | PASS structural |
| Storage/garage linking | PASS structural for active 2008c body |
| Vehicle allocation / effective fleet | PASS structural |
| Per-trip service level | PASS structural |
| `Cria_1` return insertion | ANALYZED, not yet executable in reference core |
| `Cria_2` return insertion | ANALYZED, not yet executable in reference core |
| Fine adjustment | ANALYZED, not yet executable |
| Metrics/costs | NEXT |
| Crew scheduling | PARTIAL archaeology |
| Historical executable identity | UNKNOWN |

## Next computational gate

1. characterize and reconstruct the operationally relevant behavior of `Cria_1` and `Cria_2` without propagating BC-006/BC-008 silently;
2. reconstruct projected occupancy and result metrics formula-by-formula;
3. add an in-memory end-to-end fixture proving:
   `demand → timetable → attributes → links → block → fleet → service level → indicators`;
4. only after those contracts stabilize, freeze the first PostgreSQL schema for scenarios, planned trips, links, vehicle blocks, result snapshots and provenance.
