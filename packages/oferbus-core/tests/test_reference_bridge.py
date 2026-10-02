from __future__ import annotations

from dataclasses import replace

import pytest

from oferbus_core import (
    CostPlanningInput,
    DirectionPlanningInput,
    ObservedTripInput,
    PlanningInput,
    PlanningSpecification,
    ReferencePlanningAdapter,
    SemanticLayer,
    VehiclePlanningInput,
    fingerprint,
    planning_result_fingerprint,
    validate_planning_input,
)


def fixture_input(layer: SemanticLayer = SemanticLayer.NORMALIZED) -> PlanningInput:
    start, end = 60, 120
    total = end - start + 1
    return PlanningInput(
        semantic_layer=layer,
        directions=(
            DirectionPlanningInput(
                direction_key="outbound",
                legacy_direction_number=1,
                observations=(
                    ObservedTripInput(60, 10, critical_passengers=10, travel_time_min=10),
                    ObservedTripInput(90, 10, critical_passengers=10, travel_time_min=10),
                    ObservedTripInput(120, 10, critical_passengers=10, travel_time_min=10),
                ),
                demand_passengers_per_minute=tuple([0.0] + [1.0] * total + [0.0]),
                renewal_index_curve=tuple([0.0] + [1.0] * total + [0.0]),
                travel_time_min_curve=tuple([0.0] + [10.0] * total + [0.0]),
                service_start_minute=start,
                service_end_minute=end,
                demand_maximum_passengers_per_minute=1.0,
                extension_km=8.0,
                storage_at_departure_terminal=True,
            ),
        ),
        vehicle=VehiclePlanningInput(seats=20, free_area_m2=10.0, capacity_level=1),
        cost=CostPlanningInput(mode="per_km", cost_per_km=2.0),
        specification=PlanningSpecification(
            max_headway_min=20,
            project_capacity_passengers=10.0,
            valley_capacity_passengers=10.0,
            boarding_seconds_per_passenger=0.0,
            alighting_seconds_per_passenger=0.0,
            radial=False,
        ),
    )


def test_reference_bridge_executes_characterized_normalized_slice() -> None:
    planning_input = fixture_input()
    result = ReferencePlanningAdapter().execute(planning_input)

    assert result.semantic_layer is SemanticLayer.NORMALIZED
    assert result.engine_id == "reference-bridge"
    assert result.input_fingerprint == fingerprint(planning_input)
    assert len(result.output_fingerprint) == 64
    assert result.output_fingerprint == planning_result_fingerprint(result)
    assert result.trips
    assert result.effective_fleet >= 1
    assert all(item.vehicle_block > 0 for item in result.trips)
    assert all(item.service_level is not None for item in result.trips)
    assert result.metrics.total_trips == len(result.trips)
    assert result.metrics.effective_fleet == result.effective_fleet
    assert 0 <= (result.metrics.mean_occupancy_rate or 0) <= 1
    assert result.metrics.daily_total_cost == pytest.approx(result.metrics.total_distance_km * 2.0)
    assert result.metrics.distance_semantics == "direction-weighted"


def test_same_input_produces_same_fingerprints() -> None:
    adapter = ReferencePlanningAdapter()
    first = adapter.execute(fixture_input())
    second = adapter.execute(fixture_input())
    assert first.input_fingerprint == second.input_fingerprint
    assert first.output_fingerprint == second.output_fingerprint


def test_legacy_exact_exposes_legacy_distance_semantics() -> None:
    result = ReferencePlanningAdapter().execute(fixture_input(SemanticLayer.LEGACY_EXACT))
    assert result.metrics.distance_semantics == "legacy-total-trips-times-mean-extension"
    assert any("return passenger-replay defect" in note for note in result.provenance_notes)


def test_validation_rejects_short_curves() -> None:
    planning_input = fixture_input()
    direction = planning_input.directions[0]
    broken = replace(
        planning_input,
        directions=(replace(direction, demand_passengers_per_minute=(0.0, 1.0, 0.0)),),
    )
    with pytest.raises(ValueError, match="demand curve"):
        validate_planning_input(broken)


def test_modern_layer_is_not_faked() -> None:
    with pytest.raises(NotImplementedError, match="modern semantic layer"):
        ReferencePlanningAdapter().execute(fixture_input(SemanticLayer.MODERN))
