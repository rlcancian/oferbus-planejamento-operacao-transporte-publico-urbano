import pytest

from oferbus_legacy_core import *


def test_reference_pipeline_end_to_end_single_direction():
    start, end = 60, 120
    total = end - start + 1
    observations = (
        TripObservation(60, 10, critical_passengers=10, travel_time=10),
        TripObservation(90, 10, critical_passengers=10, travel_time=10),
        TripObservation(120, 10, critical_passengers=10, travel_time=10),
    )
    demand = tuple([0.0] + [1.0] * total + [0.0])
    ir = tuple([0.0] + [1.0] * total + [0.0])
    tt = tuple([0.0] + [10.0] * total + [0.0])
    direction = DirectionPlanningData(
        observed=observations,
        demand_curve=demand,
        ir_curve=ir,
        travel_time_curve=tt,
        start=start,
        end=end,
        maximum=1.0,
        storage_at_departure_terminal=True,
    )
    cfg = MinimumTimetableConfig(
        max_interval=20,
        project_capacity=10.0,
        valley_capacity=10.0,
        boarding_seconds=0.0,
        alighting_seconds=0.0,
        radial=False,
    )

    planned = minimum_timetable_2007_legacy({1: direction}, cfg)
    operational = complete_trip_attributes_legacy(planned, directions={1: direction}, config=cfg)
    fleet = build_basic_link_graph_legacy(operational, radial=False)
    vehicle = VehicleModel(seats=20, free_area_m2=10.0)
    vehicle_models = {v: vehicle for v in range(1, fleet + 1)}
    assign_service_levels_legacy(
        operational,
        demand_curves={1: demand},
        ir_curves={1: ir},
        direction_starts={1: start},
        vehicle_models=vehicle_models,
    )
    occupancy = projected_mean_occupancy_rate_normalized(
        operational,
        demand_curves={1: demand},
        ir_curves={1: ir},
        direction_starts={1: start},
        vehicle_models=vehicle_models,
        default_vehicle=vehicle,
        capacity_level=1,
    )
    metrics = calculate_project_metrics_legacy(
        operational,
        total_passengers_by_direction={1: int(sum(demand[1:-1]))},
        extension_km_by_direction={1: 8.0},
        effective_fleet=fleet,
        mean_renewal_index=1.0,
        mean_occupancy_rate=occupancy,
        cost=CostParameters("per_km", cost_per_km=2.0),
        typical_day_participation=1.0,
        equivalent_passenger_index=1.0,
    )

    assert planned
    assert operational
    assert fleet >= 1
    assert all(t.vehicle > 0 for t in operational)
    assert all(t.service_level is not None for t in operational)
    assert 0 <= occupancy <= 1
    assert metrics.total_trips == len(operational)
    assert metrics.effective_fleet == fleet
    assert metrics.daily_total_cost == pytest.approx(metrics.total_distance_km * 2.0)
