# OferBus — Results, Occupancy and Costs Characterization v0.2

Date: 2026-10-02

## Purpose

This revision corrects the domain interpretation of legacy **viagens expressas** and formalizes the split between `legacy-exact` and `normalized` result semantics.

## Domain clarification: express trip

**CONFIRMED BY USER / CONSISTENT WITH LEGACY WORST-OCCUPANCY CODE**

A legacy OferBus `viagem expressa` is an operational/deadhead movement created because a vehicle is needed at another terminal. It transports **zero passengers**.

Consequences:

1. it contributes zero passenger load and zero critical-section passenger load;
2. it must still count as an operated trip when measuring overall projected occupancy, because vehicle resources are consumed;
3. passenger demand that accumulates while the vehicle performs the express movement remains available for the next normal passenger-service trip.

## Two modern occupancy indicators

### 1. Projected mean occupancy rate

This is the system-level indicator. Express trips remain in the denominator with zero occupancy. Therefore necessary deadhead movements reduce the projected average occupancy, as they should.

### 2. Projected mean operational occupancy rate

Proposed new modern indicator. It excludes express trips from the denominator and therefore measures only passenger-service trips.

This metric did not exist as a distinct historical OferBus result and belongs to the `normalized` layer.

## BC-010 — Bug Candidate 010

The previous interpretation of BC-010 was too broad. Inclusion of express trips in the denominator is **not a defect**.

The candidate defect is narrower:

`Calcula_Taxa_Ocupacao_Projetada` in the 2008c source iterates over every trip without testing the express bit. It therefore assigns the demand interval to an express trip and advances the previous-departure marker.

This contradicts the domain definition that express trips carry zero passengers and also differs from the behavior of `Calcula_Pior_Ocupacao_Projetada`, which explicitly gives express trips zero passengers and preserves the previous normal-trip marker.

The reference core now exposes three distinct computations:

- `projected_mean_occupancy_rate_legacy`: exact 2008c behavior;
- `projected_mean_occupancy_rate_normalized`: express trip = zero passengers, included in denominator;
- `projected_mean_operational_occupancy_rate_normalized`: express trip excluded from denominator.

A characterization fixture uses different vehicle capacities to prove that BC-010 can change the resulting average. With equal capacities and constant IR, redistribution of the same accumulated demand can cancel algebraically and hide the defect.

## Other result-layer finding retained

**BC-005 — Bug Candidate 005:** projected radial total distance uses `total trips × mean directional extension` instead of direction-weighted mileage. The reference core keeps both legacy-exact and corrected variants.

## Architectural consequence

The future OferBus should persist both the semantic layer and algorithm version that produced each result. A result snapshot must identify whether it came from a legacy-compatible or normalized model; modern corrections must never overwrite historical reproducibility.
