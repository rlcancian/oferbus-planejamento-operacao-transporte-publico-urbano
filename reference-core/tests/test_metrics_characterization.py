import pytest

from oferbus_legacy_core.metrics import (
    CostParameters,
    calculate_observed_metrics_legacy,
    calculate_project_metrics_distance_corrected,
    calculate_project_metrics_legacy,
    monthly_cost_legacy,
    projected_mean_occupancy_rate_legacy,
    projected_worst_occupancy_legacy,
)
from oferbus_legacy_core.occupancy_semantics import (
    projected_mean_occupancy_rate_normalized,
    projected_mean_operational_occupancy_rate_normalized,
)
from oferbus_legacy_core.model import TripObservation, VehicleModel
from oferbus_legacy_core.operations import OperationalTrip, TripTypeFlag


def _trip(direction, departure, arrival, *, vehicle=1, express=False):
    return OperationalTrip(
        direction=direction,
        real_departure=departure,
        virtual_departure=departure,
        real_arrival=arrival,
        virtual_arrival=arrival,
        trip_type=int(TripTypeFlag.EXPRESS) if express else 0,
        vehicle=vehicle,
    )


def test_observed_radial_distance_is_direction_weighted():
    observations = {
        1: [TripObservation(60, 20, travel_time=20), TripObservation(90, 20, travel_time=20)],
        2: [TripObservation(70, 20, travel_time=40)],
    }
    m = calculate_observed_metrics_legacy(
        observations,
        extension_km_by_direction={1: 10.0, 2: 20.0},
        available_fleet=2,
        mean_renewal_index=2.0,
        cost=CostParameters("per_km", cost_per_km=2.0),
        typical_day_participation=1.0,
        equivalent_passenger_index=1.0,
    )
    assert m.total_distance_km == pytest.approx(40.0)
    assert m.mean_extension_km == pytest.approx(15.0)
    assert m.daily_total_cost == pytest.approx(80.0)


def test_bc005_projected_distance_differs_when_direction_counts_are_asymmetric():
    trips = [_trip(1, 60, 80), _trip(1, 90, 110), _trip(2, 120, 160)]
    kwargs = dict(
        total_passengers_by_direction={1: 40, 2: 20},
        extension_km_by_direction={1: 10.0, 2: 20.0},
        effective_fleet=2,
        mean_renewal_index=2.0,
        mean_occupancy_rate=0.5,
        cost=CostParameters("per_km", cost_per_km=2.0),
        typical_day_participation=1.0,
        equivalent_passenger_index=1.0,
    )
    legacy = calculate_project_metrics_legacy(trips, **kwargs)
    corrected = calculate_project_metrics_distance_corrected(trips, **kwargs)
    assert legacy.total_distance_km == pytest.approx(45.0)
    assert corrected.total_distance_km == pytest.approx(40.0)
    assert legacy.daily_total_cost == pytest.approx(90.0)
    assert corrected.daily_total_cost == pytest.approx(80.0)


def test_fixed_variable_cost_branch_matches_legacy_formula():
    trips = [_trip(1, 60, 80), _trip(1, 90, 110)]
    m = calculate_project_metrics_legacy(
        trips,
        total_passengers_by_direction={1: 40},
        extension_km_by_direction={1: 10.0},
        effective_fleet=2,
        mean_renewal_index=2.0,
        mean_occupancy_rate=0.4,
        cost=CostParameters("fixed_variable", fixed_cost_per_vehicle=100.0, variable_cost_per_km=3.0),
        typical_day_participation=0.5,
        equivalent_passenger_index=1.0,
    )
    assert m.total_distance_km == pytest.approx(20.0)
    assert m.daily_total_cost == pytest.approx(20.0 * 3.0 + 2 * 0.5 * 100.0)


def test_equivalent_passenger_index_scales_cost_per_passenger():
    trips = [_trip(1, 60, 80), _trip(1, 90, 110)]
    m = calculate_project_metrics_legacy(
        trips,
        total_passengers_by_direction={1: 100},
        extension_km_by_direction={1: 10.0},
        effective_fleet=1,
        mean_renewal_index=2.0,
        mean_occupancy_rate=0.5,
        cost=CostParameters("per_km", cost_per_km=5.0),
        typical_day_participation=1.0,
        equivalent_passenger_index=0.8,
    )
    assert m.daily_total_cost == pytest.approx(100.0)
    assert m.cost_per_equivalent_passenger == pytest.approx((100.0 / 100.0) / 0.8)


def test_monthly_cost_uses_recovered_typical_day_constants():
    expected = 100.0 * (365.25 / 12.0 / 7.0) * 4.8358
    assert monthly_cost_legacy(100.0, 0) == pytest.approx(expected)


def test_worst_projected_occupancy_ignores_express_and_keeps_previous_normal_marker():
    trips = [_trip(1, 60, 70), _trip(1, 70, 80, express=True), _trip(1, 80, 90)]
    demand = {1: tuple([0.0] + [1.0] * 21 + [0.0])}
    ir = {1: tuple([0.0] + [1.0] * 21 + [0.0])}
    vehicle = VehicleModel(0, 10.0)
    r = projected_worst_occupancy_legacy(
        trips,
        demand_curves=demand,
        ir_curves=ir,
        direction_starts={1: 60},
        vehicle_models={1: vehicle},
        default_vehicle=vehicle,
    )
    assert r.maximum_passengers == 20
    assert r.maximum_passengers_departure == 80
    assert r.maximum_critical_density == pytest.approx(2.0)


def test_bc010_legacy_assigns_passenger_demand_to_express_but_normalized_sets_zero():
    trips = [_trip(1, 60, 70, vehicle=1), _trip(1, 70, 80, vehicle=2, express=True), _trip(1, 80, 90, vehicle=1)]
    demand = {1: tuple([0.0] + [1.0] * 21 + [0.0])}
    ir = {1: tuple([0.0] + [1.0] * 21 + [0.0])}
    vehicle = VehicleModel(10, 10.0)
    express_vehicle = VehicleModel(70, 20.0)
    legacy = projected_mean_occupancy_rate_legacy(
        trips, demand_curves=demand, ir_curves=ir, direction_starts={1: 60},
        vehicle_models={1: vehicle, 2: express_vehicle}, default_vehicle=vehicle, capacity_level=1,
    )
    normalized = projected_mean_occupancy_rate_normalized(
        trips, demand_curves=demand, ir_curves=ir, direction_starts={1: 60},
        vehicle_models={1: vehicle, 2: express_vehicle}, default_vehicle=vehicle, capacity_level=1,
    )
    operational = projected_mean_operational_occupancy_rate_normalized(
        trips, demand_curves=demand, ir_curves=ir, direction_starts={1: 60},
        vehicle_models={1: vehicle, 2: express_vehicle}, default_vehicle=vehicle, capacity_level=1,
    )
    assert legacy == pytest.approx((1/25 + 10/100 + 10/25) / 3)
    assert normalized == pytest.approx((1/25 + 0 + 20/25) / 3)
    assert operational == pytest.approx((1/25 + 20/25) / 2)
    assert legacy != normalized != operational


def test_legacy_speed_uses_mean_extension_over_mean_trip_time():
    trips = [_trip(1, 60, 80), _trip(2, 90, 130)]
    m = calculate_project_metrics_legacy(
        trips,
        total_passengers_by_direction={1: 20, 2: 20},
        extension_km_by_direction={1: 10.0, 2: 20.0},
        effective_fleet=1,
        mean_renewal_index=2.0,
        mean_occupancy_rate=0.5,
        cost=CostParameters("per_km", cost_per_km=1.0),
        typical_day_participation=1.0,
        equivalent_passenger_index=1.0,
    )
    assert m.mean_travel_time_min == pytest.approx(30.0)
    assert m.mean_speed_kmh == pytest.approx(30.0)
