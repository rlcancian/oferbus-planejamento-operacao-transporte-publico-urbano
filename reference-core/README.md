# OferBus Computational Reconstruction Reference v0.3

This is an **archaeological/characterization harness**, not the final OferBus architecture. It ports source-confirmed behavior from the 2008c Visual Basic code into small, deterministic Python components so historical semantics can be tested independently of UI, persistence, or any future web stack.

Python is being used here as a scientific reconstruction language only. It is not yet a binding decision for the production architecture.

## Implemented

### Demand and capacity

- `LEG-DMD-001` passengers/minute;
- `LEG-DMD-002` original minute curve;
- `LEG-DMD-003` legacy 10-minute aggregation + moving-average adjustment;
- `LEG-DMD-004` mass correction;
- `LEG-SCH-001` robust maximum;
- `LEG-CAP-001` capacity levels, including explicit preservation of the candidate default-vehicle defect and a separate corrected variant;
- fleet reserve with historical rounding semantics.

### Forecasting

- parabola, logarithmic and exponential >=3-year regression branch;
- historical DQM/MSE-based model selection.

### Time, renewal and MPTDC

- TPV interpolation and smoothing;
- explicit legacy/corrected variants for the final `-2` sentinel anomaly;
- constant and variable renewal-index curves;
- code-2008c and Manual-2005 MPTDC variants maintained separately.

### Minimum timetable

`minimum_timetable_2007_legacy` reconstructs `MMARCHA1.Calcula_Quadro_Horarios_Minimo_2007`: minute-by-minute passenger accumulation, capacity/IR, maximum headway, terminals with/without storage, return trips, final anchoring and tail regularization. The return passenger-replay indexing defect can be preserved or corrected explicitly.

### Complete operational trip and graph

- normal and express complete-trip attributes;
- named reconstruction of the `Tipo` bitfield;
- typed entry/exit links replacing the opaque packed `Vinculos` integer internally;
- direct trip linking;
- storage linking;
- garage completion;
- logical vehicle assignment and vehicle blocks;
- effective fleet size derived from those blocks;
- per-trip service-level calculation, including historical `F1+ → 5` information loss.

Still pending for the complete historical march-diagram pipeline are `Cria_1`, `Cria_2`, `Verifica_Ida_Garagem` and fine adjustment. They are being reconstructed separately because the recovered source contains candidate defects in those stages.

## Validation

Run:

```bash
python -m pytest -q
python -m compileall -q src tests
```

Current result: **28 tests passing** and compileall **PASS**.

These are source-derived characterization/specification fixtures. A passing suite demonstrates conformance with the currently recovered contracts; it does **not** yet prove numerical identity with an executable historical OferBus binary.
