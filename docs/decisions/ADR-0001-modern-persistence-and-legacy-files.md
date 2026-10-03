# ADR-0001 — Modern persistence and legacy file formats

- **Status:** Accepted
- **Date:** 2026-10-02

## Context

The historical OferBus persisted projects through multiple proprietary file formats created under the constraints of the 1990s/2000s desktop implementation. Those formats are valuable as archaeological evidence and may contain historical project data, but they are not requirements for the rematerialized system.

## Decision

1. The modern OferBus will persist operational/domain state in **PostgreSQL**.
2. Historical `.OFB/.LEV/.RST/...` formats will **not** be used as primary storage.
3. The production domain model and database schema will **not** reproduce historical record layouts, packing, fixed-array limits, path conventions, or file decomposition.
4. Legacy files may be supported by a **one-time/administrative migration tool** if recovering historical data remains useful.
5. Such an importer must translate into the modern domain and PostgreSQL schema; it must not make the modern system dependent on continued legacy-format compatibility.
6. Export back to proprietary OferBus formats is not a parity requirement.
7. Archaeological format analysis should continue only when it provides evidence needed to recover domain semantics, algorithms, or useful historical data.

## Consequences

- The reconstructed domain, computational models and provenance requirements drive the database design.
- Legacy parsing code, if created, belongs at an anti-corruption/migration boundary and can eventually be retired.
- Binary compatibility does not constrain the new architecture.
- Golden-master validation may use historical files as test inputs without turning those formats into application contracts.
