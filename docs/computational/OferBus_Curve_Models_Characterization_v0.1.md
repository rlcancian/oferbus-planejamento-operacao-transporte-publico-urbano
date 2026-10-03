# OferBus — Characterization of TPV, IR and MPTDC v0.1

Date: 2026-10-02  
Status: source-backed computational characterization; not a production-model specification.

## Scope

This note closes the current characterization pass for three curve models used by the legacy planning pipeline:

- TPV — travel-time distribution;
- IR — renewal-index distribution;
- MPTDC — typical constant-demand periods.

Primary code evidence: `MPROCEDI.BAS` (`Calcula_Org_Tmp`, `Realiza_Ajuste_De_Curvas`, `Ajusta_Uma_Curva`) and `MGERAL.BAS` (`Calcula_Periodos_Tipicos`, `Inicializa_Ajustamentos_Para_Periodo`) in `ofb2008c`. Documentation evidence: `MANUAL_DO_OFERBUS_2005.DOC`, sections 6.2.1, 6.2.2, 6.3 and the renewal-index section.

## TPV

### Confirmed semantics

`Calcula_Org_Tmp` transforms sparse observed trip travel times into a minute-indexed curve by linear interpolation between valid observations. Missing values are represented by `-1`; synthetic beginning/end boundary markers use `-2`.

A missing initial observation is backfilled from the first valid observation. This behavior is now covered by an executable characterization test.

### BC-003 — terminal sentinel condition

The 2008c source contains:

```text
If Flag(Qui) = 2 Then
    Flag(Qui) = Flag(Qui - 1)
End If
```

The synthetic missing-end marker is `-2`, so the condition is strongly consistent with a missing minus sign.

Observable consequences are now characterized independently:

1. a trailing missing travel time (`-2`) is not repaired;
2. a legitimate final travel time of exactly `2` minutes is replaced by the previous value.

The reference core therefore retains two explicit modes:

- `preserve_sentinel_bug=True`: source-observed 2008c behavior;
- `preserve_sentinel_bug=False`: candidate correction using `-2`.

No silent correction is made.

## IR

### Confirmed semantics

When `CodIndiceRenova = 0`, the IR distribution is constant and equal to `gIdent.IndiceRenova` before the common smoothing stage.

Otherwise the code reconstructs critical-section passenger flow minute by minute and computes:

`IR(t) = demand_original(t) / critical_flow(t)`

with two guards:

- if critical flow is zero, `IR(t) = 1`;
- any calculated `IR(t) < 1` is clamped to `1`.

The stored mean IR is the arithmetic mean of the clamped original IR curve, before the later adjusted-curve smoothing.

New characterization tests cover the lower bound and the constant-IR branch.

## MPTDC

### Confirmed 2008c per-direction semantics

The active 2008c path temporarily forces the daily-demand MDV adjustment level to `2`, then invokes `Calcula_Periodos_Tipicos`.

For one direction, the relevant behavior is:

1. truncate the adjusted crossing curve to two decimal places using `Int(x*100)/100`;
2. derive the maximum from that curve;
3. use `AjustePeriodo * 2` horizontal bands;
4. detect only strict upward/downward crossings of internal thresholds;
5. discard a newly detected boundary when it is at most 30 minutes after the previous retained boundary;
6. append the final minute explicitly;
7. assign to each period the arithmetic mean of the **original demand curve** (`CurvaOrgDmn`), not the smoothed crossing curve.

The reference implementation is intentionally per-direction and now has executable tests confirming period means and the 30-minute suppression rule.

### Manual-2005 divergence

The manual documents a different variant:

- intermediate MDV adjustment degree `3`;
- number of horizontal bands equal to the selected degree `n`;
- `n` in `[2, 9]`.

The reference core keeps `manual-2005` and `code-2008c` as separate semantic variants.

### BC-009 — radial cross-direction shared-state behavior

`Calcula_Periodos_Tipicos` contains a source-level cross-direction anomaly for radial lines:

- `Inicializa_Ajustamentos_Para_Periodo` computes `Maxi` using the global active `gSentido` only;
- `Faixa()` is one-dimensional;
- the first `For sent = 1 To Radial_Ou_Circular()` overwrites the same `Faixa()` values for each direction;
- the following loop then uses the shared `Faixa()` while processing all directions.

Because `Realiza_Ajuste_De_Curvas` calls this procedure from inside its own per-direction loop, final behavior can depend on call order, the second direction's adjustment parameter, and global state.

Classification: **strong candidate defect / cross-direction contamination**. The normalized per-direction reference model does not reproduce this anomaly. A source-exact radial compatibility variant should only be implemented if a historical golden master requires it.

## Verification

Reference-core validation after this pass:

```text
python -m pytest -q
....................................
36 passed

python -m compileall -q src tests
PASS
```

## Gate

| Model | Status |
|---|---|
| TPV interpolation | PASS structural |
| TPV missing-start behavior | PASS characterized |
| TPV terminal `2` / `-2` defect | PASS characterized, correction kept separate |
| IR variable model | PASS structural |
| IR lower bound `>= 1` | PASS characterized |
| IR constant model | PASS characterized |
| MPTDC 2008c per-direction model | PASS structural |
| MPTDC Manual-2005 variant | PASS structural/documented |
| MPTDC 30-minute boundary suppression | PASS characterized |
| MPTDC period averaging from original demand | PASS characterized |
| MPTDC radial shared-state behavior | DEFECT CANDIDATE; source-confirmed structure, no normalized reproduction |

## Next computational unit

Proceed to result metrics and costs, unless a historical golden master is supplied that requires source-exact replication of BC-009.
