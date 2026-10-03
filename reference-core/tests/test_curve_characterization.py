import pytest

from oferbus_legacy_core import (
    TripObservation,
    passengers_per_minute,
    original_curve,
    renewal_index_curves_legacy,
    travel_time_curve_legacy,
    typical_periods_code_2008,
)


def test_tpv_missing_initial_observation_is_backfilled_from_first_valid_value():
    trips = [
        TripObservation(60, 10, travel_time=0),
        TripObservation(70, 10, travel_time=20),
        TripObservation(80, 10, travel_time=30),
    ]
    curve = travel_time_curve_legacy(trips)
    assert curve[1] == pytest.approx(20.0)
    assert curve[11] == pytest.approx(20.0)
    assert curve[21] == pytest.approx(30.0)


def test_tpv_source_condition_corrupts_a_genuine_final_value_of_two_minutes():
    trips = [
        TripObservation(60, 10, travel_time=10),
        TripObservation(70, 10, travel_time=20),
        TripObservation(80, 10, travel_time=2),
    ]
    legacy = travel_time_curve_legacy(trips, preserve_sentinel_bug=True)
    corrected = travel_time_curve_legacy(trips, preserve_sentinel_bug=False)
    # MPROCEDI.Calcula_Org_Tmp tests Flag(Qui) = 2, not -2.
    # Therefore a legitimate final observation of exactly 2 is replaced by the previous value.
    assert legacy[21] == pytest.approx(20.0)
    assert corrected[21] == pytest.approx(2.0)


def test_variable_ir_is_clamped_to_one_when_critical_flow_exceeds_total_flow():
    trips = [
        TripObservation(60, 10, critical_passengers=20),
        TripObservation(70, 10, critical_passengers=20),
        TripObservation(80, 10, critical_passengers=20),
    ]
    demand = original_curve(trips, passengers_per_minute(trips))
    result = renewal_index_curves_legacy(
        trips, demand_original=demand, adjustment_level=1
    )
    assert result.mean == pytest.approx(1.0)
    assert all(v == pytest.approx(1.0) for v in result.original[1:-1])


def test_constant_ir_branch_remains_constant_after_legacy_adjustment():
    trips = [
        TripObservation(60, 10),
        TripObservation(70, 10),
        TripObservation(80, 10),
    ]
    demand = original_curve(trips, passengers_per_minute(trips))
    result = renewal_index_curves_legacy(
        trips, demand_original=demand, adjustment_level=1, constant_ir=2.5
    )
    assert result.mean == pytest.approx(2.5)
    assert all(v == pytest.approx(2.5) for v in result.original[1:-1])
    assert all(v == pytest.approx(2.5) for v in result.adjusted[1:-1])


def test_mptdc_segment_values_are_means_of_original_not_smoothed_crossing_curve():
    raw = [0.0] + [2.0] * 45 + [12.0] * 50 + [4.0] * 45 + [0.0]
    result = typical_periods_code_2008(raw, period_adjustment=2)
    boundaries = result.boundaries
    assert boundaries[0] == 1
    assert boundaries[-1] == len(raw) - 2

    # Boundaries are detected on the adjusted curve, but each resulting period
    # receives the arithmetic mean of CurvaOrgDmn (the original demand curve).
    first_a, first_b = boundaries[0], boundaries[1]
    expected = sum(raw[first_a:first_b + 1]) / (first_b - first_a + 1)
    assert all(result.curve[i] == pytest.approx(expected) for i in range(first_a, first_b + 1))

    for k in range(2, len(boundaries)):
        a = boundaries[k - 1] + 1
        b = boundaries[k]
        expected = sum(raw[a:b + 1]) / (b - a + 1)
        assert all(result.curve[i] == pytest.approx(expected) for i in range(a, b + 1))


def test_mptdc_detected_crossing_boundaries_respect_legacy_30_minute_suppression():
    raw = [0.0] + [2.0] * 40 + [12.0] * 40 + [2.0] * 40 + [12.0] * 40 + [0.0]
    result = typical_periods_code_2008(raw, period_adjustment=2)
    internal = result.boundaries[:-1]
    assert all((b - a) > 30 for a, b in zip(internal, internal[1:]))
