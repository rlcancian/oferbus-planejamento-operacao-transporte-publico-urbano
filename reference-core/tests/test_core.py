import math
import pytest
from oferbus_legacy_core import *
from oferbus_legacy_core.numeric import legacy_round_gt_half


def test_legacy_round_half_is_not_bankers_rounding():
    assert legacy_round_gt_half(2.5) == 2
    assert legacy_round_gt_half(2.50001) == 3


def test_passengers_per_minute_regular_intervals():
    trips = [TripObservation(60, 10), TripObservation(70, 20), TripObservation(80, 30)]
    ppm = passengers_per_minute(trips)
    assert ppm[2] == pytest.approx(2.0)
    assert ppm[3] == pytest.approx(3.0)


def test_original_curve_is_stepwise_between_departures():
    trips = [TripObservation(60, 10), TripObservation(70, 20), TripObservation(80, 30)]
    ppm = passengers_per_minute(trips)
    c = original_curve(trips, ppm)
    assert all(v == pytest.approx(2.0) for v in c[1:12])
    assert all(v == pytest.approx(3.0) for v in c[12:22])


def test_capacity_bug_is_explicitly_preserved_and_corrected_variant_differs():
    default = VehicleModel(40, 10.0)
    requested = VehicleModel(20, 4.0)
    legacy = capacity_levels_legacy(default, requested)
    corrected = capacity_levels_corrected(requested)
    assert legacy[5] == pytest.approx(115.0)
    assert corrected[5] == pytest.approx(50.0)
    assert legacy != corrected


def test_fleet_reserve_uses_legacy_gt_half_rounding():
    assert fleet_reserve_legacy(10, 25) == 2
    assert fleet_reserve_legacy(11, 25) == 3


def test_robust_maximum_suppresses_single_point_spike():
    c = [0.0] + [10.0] * 20 + [0.0]
    c[10] = 80.0
    m = robust_maximum_legacy(c)
    assert m < 80.0
    assert m == pytest.approx((10*6 + 80)/7)


def test_mass_correction_preserves_requested_total_with_legacy_first_point_convention():
    c = [0.0] + [1.0] * 20 + [0.0]
    fixed = correct_adjusted_curve_legacy(c, original_sum=100.0, first_point=10)
    assert 10 + sum(fixed[2:-1]) == pytest.approx(100.0)
    assert fixed[1] == pytest.approx(fixed[2])


def test_virtual_times_use_load_ir_and_strict_half_rounding():
    demand = [0.0, 100.0, 0.0]
    ir = [0.0, 2.0, 0.0]
    tt = [0.0, 30.0, 0.0]
    dep = virtual_departure_legacy(real_departure=60, start=60, end=60, demand_curve=demand, ir_curve=ir,
                                   maximum=100.0, project_capacity=50.0, valley_capacity=30.0,
                                   boarding_seconds=2.5)
    arr = virtual_arrival_legacy(real_departure=60, start=60, end=60, demand_curve=demand, ir_curve=ir,
                                 travel_time_curve=tt, maximum=100.0, project_capacity=50.0,
                                 valley_capacity=30.0, alighting_seconds=2.0)
    assert dep == 56
    assert arr == 93


def test_forecast_prefers_parabola_for_exact_quadratic_annual_means():
    annual = [100 + 3*i + 2*i*i for i in range(1, 6)]
    monthly = [y for y in annual for _ in range(12)]
    r = fit_forecasts_legacy(monthly)
    expected_next = 100 + 3*6 + 2*6*6
    assert r.forecasts[0] == pytest.approx(expected_next, rel=1e-10)
    assert r.mse[0] == pytest.approx(0.0, abs=1e-10)
    assert r.best_model == 1


def test_travel_time_curve_interpolates_observed_tpv():
    trips = [
        TripObservation(60, 10, travel_time=10),
        TripObservation(70, 10, travel_time=20),
        TripObservation(80, 10, travel_time=30),
    ]
    c = travel_time_curve_legacy(trips)
    assert c[1] == pytest.approx(10.0)
    assert c[6] == pytest.approx(15.0)
    assert c[11] == pytest.approx(20.0)
    assert c[21] == pytest.approx(30.0)


def test_travel_time_final_missing_sentinel_bug_is_characterized():
    trips = [
        TripObservation(60, 10, travel_time=10),
        TripObservation(70, 10, travel_time=20),
        TripObservation(80, 10, travel_time=0),
    ]
    legacy = travel_time_curve_legacy(trips, preserve_sentinel_bug=True)
    corrected = travel_time_curve_legacy(trips, preserve_sentinel_bug=False)
    assert legacy[21] == pytest.approx(-2.0)
    assert corrected[21] == pytest.approx(20.0)


def test_variable_renewal_index_from_passengers_and_critical_section():
    trips = [
        TripObservation(60, 10, critical_passengers=5),
        TripObservation(70, 20, critical_passengers=10),
        TripObservation(80, 30, critical_passengers=15),
    ]
    ppm = passengers_per_minute(trips)
    demand = original_curve(trips, ppm)
    r = renewal_index_curves_legacy(trips, demand_original=demand, adjustment_level=1)
    assert r.mean == pytest.approx(2.0)
    assert all(v == pytest.approx(2.0) for v in r.original[1:-1])


def test_mptdc_code_and_manual_are_versioned_as_distinct_semantics():
    raw = [0.0]
    raw += [2.0] * 40 + [10.0] * 40 + [2.0] * 40 + [0.0]
    code = typical_periods_code_2008(raw, period_adjustment=2)
    manual = typical_periods_manual_2005(raw, degree=2)
    assert code.semantic_variant == "code-2008c"
    assert manual.semantic_variant == "manual-2005"
    assert code.number_of_bands == 4
    assert manual.number_of_bands == 2
    assert code.thresholds != manual.thresholds


def test_minimum_timetable_storage_terminal_constant_demand():
    start, end = 60, 120
    total = end - start + 1
    demand = tuple([0.0] + [1.0] * total + [0.0])
    ir = tuple([0.0] + [1.0] * total + [0.0])
    tt = tuple([0.0] + [10.0] * total + [0.0])
    observed = (TripObservation(start, 1), TripObservation(end, 1))
    d = DirectionPlanningData(observed, demand, ir, tt, start, end, 10.0, True)
    cfg = MinimumTimetableConfig(
        max_interval=20, project_capacity=10.0, valley_capacity=10.0,
        boarding_seconds=0.0, alighting_seconds=0.0, radial=False,
    )
    trips = minimum_timetable_2007_legacy({1: d}, cfg)
    departures = [t.real_departure for t in trips]
    assert departures[0] == 60
    assert departures[-1] == 120
    assert departures[:4] == [60, 70, 80, 90]


def test_minimum_timetable_max_interval_binds_before_capacity():
    start, end = 60, 120
    total = end - start + 1
    demand = tuple([0.0] + [0.1] * total + [0.0])
    ir = tuple([0.0] + [1.0] * total + [0.0])
    tt = tuple([0.0] + [10.0] * total + [0.0])
    observed = (TripObservation(start, 1), TripObservation(end, 1))
    d = DirectionPlanningData(observed, demand, ir, tt, start, end, 100.0, True)
    cfg = MinimumTimetableConfig(
        max_interval=15, project_capacity=100.0, valley_capacity=100.0,
        boarding_seconds=0.0, alighting_seconds=0.0, radial=False,
    )
    trips = minimum_timetable_2007_legacy({1: d}, cfg)
    assert [t.real_departure for t in trips][:4] == [60, 75, 90, 105]


def _op(direction, dep, arr, *, trip_type=0):
    return OperationalTrip(direction, dep, dep, arr, arr, trip_type=trip_type)


def test_legacy_link_encoding_has_explicit_entry_and_exit_semantics():
    assert encode_legacy_links(LinkKind.TRIP, LinkKind.STORAGE) == 11
    assert decode_legacy_links(11) == (LinkKind.TRIP, LinkKind.STORAGE)
    assert encode_legacy_links(LinkKind.STORAGE, LinkKind.TRIP) == 14


def test_clear_links_preserves_manual_entry_and_exit_bits():
    t = _op(1, 60, 80, trip_type=16 | 32)
    t.entry_link = LinkKind.TRIP
    t.exit_link = LinkKind.STORAGE
    t.vehicle = 7
    clear_non_manual_links([t])
    assert t.entry_link == LinkKind.TRIP
    assert t.exit_link == LinkKind.STORAGE
    assert t.vehicle == 0


def test_direct_link_prefers_later_arrival_for_same_future_departure():
    trips = [_op(1, 60, 80), _op(1, 70, 90), _op(2, 100, 120)]
    created = link_direct_trips_legacy(trips, radial=True)
    assert created == 1
    assert trips[0].exit_link == LinkKind.NONE
    assert trips[1].exit_link == LinkKind.TRIP
    assert trips[2].entry_link == LinkKind.TRIP


def test_storage_and_garage_complete_unresolved_links():
    trips = [_op(1, 60, 80), _op(2, 100, 120)]
    assert link_storage_legacy(trips, radial=True) == 1
    link_garages_legacy(trips)
    assert trips[0].entry_link == LinkKind.GARAGE
    assert trips[0].exit_link == LinkKind.STORAGE
    assert trips[1].entry_link == LinkKind.STORAGE
    assert trips[1].exit_link == LinkKind.GARAGE


def test_fleet_allocation_follows_matching_link_chain():
    trips = [
        _op(1, 60, 80),
        _op(2, 90, 110),
        _op(1, 120, 140),
        _op(1, 65, 85),
    ]
    trips.sort(key=lambda t: t.virtual_departure)
    first = trips[0]
    independent = trips[1]
    second = trips[2]
    third = trips[3]
    first.entry_link = LinkKind.GARAGE
    first.exit_link = LinkKind.TRIP
    second.entry_link = LinkKind.TRIP
    second.exit_link = LinkKind.TRIP
    third.entry_link = LinkKind.TRIP
    third.exit_link = LinkKind.GARAGE
    independent.entry_link = LinkKind.GARAGE
    independent.exit_link = LinkKind.GARAGE
    fleet = allocate_fleet_legacy(trips, radial=True)
    assert fleet == 2
    assert first.vehicle == second.vehicle == third.vehicle
    assert independent.vehicle != first.vehicle


def test_basic_link_graph_yields_vehicle_blocks_and_fleet():
    trips = [
        _op(1, 60, 80),
        _op(2, 90, 110),
        _op(1, 120, 140),
        _op(2, 150, 170),
    ]
    fleet = build_basic_link_graph_legacy(trips, radial=True)
    blocks = vehicle_blocks(trips)
    assert fleet == 1
    assert list(blocks) == [1]
    assert len(blocks[1]) == 4
    assert trips[0].entry_link == LinkKind.GARAGE
    assert trips[-1].exit_link == LinkKind.GARAGE
