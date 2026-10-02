# OferBus Computational Reconstruction Reference v0.2

This is an **archaeological/characterization harness**, not the final OferBus architecture.
It ports source-confirmed behavior from the 2008c Visual Basic code into small,
deterministic Python components so that historical semantics can be tested independently
of UI, persistence, or any future web stack.

Python is being used here as a scientific reconstruction language only. It is not yet a
binding decision for the production architecture.

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

### Time and renewal curves

- original TPV interpolation from observed trips;
- TPV smoothing through the common legacy adjustment algorithm;
- explicit `legacy` and `corrected` variants for the final `-2` sentinel anomaly;
- constant and variable renewal-index curves;
- conversion `passengers / passengers-on-critical-section` with IR >= 1;
- adjusted IR curve.

### MPTDC

Two semantics are deliberately maintained:

- `code-2008c`: intermediate MDV level 2 and `AjustePeriodo * 2` horizontal bands;
- `manual-2005`: documented intermediate MDV level 3 and number of bands equal to the selected degree.

They are not silently reconciled because the legacy sources genuinely diverge.

### Minimum timetable

`minimum_timetable_2007_legacy` reconstructs the central procedure
`MMARCHA1.Calcula_Quadro_Horarios_Minimo_2007`, including:

- minute-by-minute passenger accumulation;
- demand-dependent effective capacity;
- renewal index;
- maximum admissible headway;
- terminals with and without storage;
- opposite-direction vehicle arrival detection;
- normal and return trips;
- optional express return trips;
- final anchor at the last observed departure;
- legacy tail-headway regularization;
- switchable preservation/correction of the passenger-replay indexing defect in return trips.

Still outside this reconstructed function are the subsequent historical stages:
`Ajeitadinha_Brasileira_Horarios`, complete trip-attribute filling, journey linking,
storage/garage linking, vehicle allocation, service-level calculation and crew scheduling.

## Validation

Run:

```bash
python -m pytest
```

Current result: **15 tests passing**.

These tests are source-derived characterization fixtures. A passing suite means the
reference implementation satisfies the current recovered contracts; it does **not** yet
prove numerical identity with an executable historical OferBus binary.
