# OferBus — Computational Reconstruction Status v0.7

Date: 2026-10-02

## Delta from v0.6

This increment advances return-trip completion and operational checks without expanding into the PostgreSQL production model yet.

Acronyms used in this checkpoint:

- **BC — Bug Candidate**: candidate defect in the legacy source.
- **QDT — Quilometragem Diária Total**: total daily operated distance.
- **IPK — Índice de Passageiros por Quilômetro**: passengers divided by operated kilometres.

## New executable coverage

### `Cria_2`

The reference core now covers:

- storage-enabled branch when the backward anchor exists;
- storage-enabled branch when the backward anchor does not exist but the forward anchor does;
- no-storage branch when all temporal anchors used by the active 2008 source exist.

The remaining no-storage fallbacks are isolated because the legacy source contains unsafe/inconsistent expressions. They are tracked as **BC-012** instead of being silently normalized.

### `Verifica_Ida_Garagem`

Reconstructed as `remove_orphan_express_returns_legacy`.

It removes a created express/deadhead trip with no exit link and clears the predecessor link that previously fed that movement.

**BC-011:** the VB routine increments the loop index after deleting the current array entry, so a consecutive removable trip can be skipped. Both exact and normalized behaviors are testable.

### `Verifica_Intervalo_4Min`

Reconstructed as `count_departure_intervals_under_four_minutes_legacy`.

It counts same-direction real-departure intervals strictly below four minutes while traversing the trip array in virtual-time order. Express/deadhead trips participate in this check.

## Validation

```text
python -m pytest -q
52 passed

python -m compileall -q src tests
PASS
```

## Current computational gate

| Area | Status |
|---|---|
| Demand reconstruction | PASS |
| Travel-time profile | PASS with legacy/corrected sentinel variants |
| Renewal index | PASS structural |
| Typical constant-demand periods | PASS structural with Manual-2005 / Code-2008 variants |
| Forecasting | PASS for characterized historical models |
| Minimum timetable | PASS structural for characterized branches |
| Trip attributes and type flags | PASS |
| Direct/storage/garage links | PASS structural |
| Vehicle blocks and effective fleet | PASS structural |
| `Cria_1` | PASS structural with explicit legacy type inconsistency |
| `Cria_2` storage path | PASS for characterized branches |
| `Cria_2` no-storage path | PARTIAL: fully anchored path PASS; BC-012 fallbacks isolated |
| One-minute fine adjustment | PASS with BC-007 exact/corrected variants |
| Orphan express/deadhead cleanup | PASS with BC-011 exact/normalized variants |
| <4-minute departure warning | PASS |
| Occupancy semantics | PASS legacy + normalized |
| Indicators and costs | PASS structural |
| End-to-end in-memory fixture | PASS |
| Historical executable numerical identity | UNKNOWN |

## Next gate

The computational model is now sufficiently stable to begin freezing the first modern persistence contract while continuing targeted legacy characterization in parallel.

The next block should therefore define the first PostgreSQL-oriented scenario/result model for:

- organizations and projects;
- lines and directions;
- scenarios and model-version provenance;
- input datasets and planning parameters;
- planned trips;
- explicit entry/exit links;
- vehicle blocks and fleet result;
- occupancy/result snapshots;
- cost snapshots;
- manual overrides and audit/provenance.

This model must not reproduce legacy file structures. It should persist the reconstructed domain directly and preserve both `legacy-exact` and `normalized` computational result variants.
