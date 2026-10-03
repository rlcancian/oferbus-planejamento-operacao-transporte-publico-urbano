from __future__ import annotations

from typing import Mapping, Sequence

from .model import VehicleModel
from .operations import OperationalTrip
from .service_level import passengers_in_period_legacy


def _capacity(vehicle: VehicleModel, capacity_level: int) -> float:
    capacity = vehicle.seats + (1.5 * capacity_level) * vehicle.free_area_m2
    if capacity <= 0:
        raise ValueError("vehicle capacity must be positive")
    return float(capacity)


def _trip_vehicle(
    trip: OperationalTrip,
    vehicle_models: Mapping[int, VehicleModel],
    default_vehicle: VehicleModel,
) -> VehicleModel:
    return vehicle_models.get(trip.vehicle, default_vehicle)


def projected_mean_occupancy_rate_normalized(
    trips_in_pipeline_order: Sequence[OperationalTrip],
    *,
    demand_curves: Mapping[int, Sequence[float]],
    ir_curves: Mapping[int, Sequence[float]],
    direction_starts: Mapping[int, int],
    vehicle_models: Mapping[int, VehicleModel],
    default_vehicle: VehicleModel,
    capacity_level: int,
) -> float:
    """Projected mean occupancy with correct express-trip domain semantics.

    A legacy OferBus ``viagem expressa`` is a deadhead/operational movement: it
    carries zero passengers. It nevertheless remains in the denominator because it
    consumes one operated trip. It also does not advance the previous normal
    passenger-service departure marker, so its demand remains for the next normal
    trip.
    """
    if not trips_in_pipeline_order:
        raise ValueError("at least one projected trip is required")

    occupancy_sum = 0.0
    directions = sorted({t.direction for t in trips_in_pipeline_order})
    for direction in directions:
        direction_trips = [t for t in trips_in_pipeline_order if t.direction == direction]
        normal = [t for t in direction_trips if not t.is_express]
        previous = normal[0].real_departure - 1 if normal else None
        for trip in direction_trips:
            if trip.is_express:
                continue
            if previous is None:
                previous = trip.real_departure - 1
            passengers = passengers_in_period_legacy(
                demand_curves[direction],
                line_start=direction_starts[direction],
                start_real=previous + 1,
                end_real=trip.real_departure,
            )
            ir_idx = trip.real_departure - direction_starts[direction] + 1
            ir = float(ir_curves[direction][ir_idx])
            if ir == 0:
                raise ZeroDivisionError("normalized projected occupancy rate divides by IR")
            vehicle = _trip_vehicle(trip, vehicle_models, default_vehicle)
            occupancy_sum += (passengers / ir) / _capacity(vehicle, capacity_level)
            previous = trip.real_departure

    return occupancy_sum / len(trips_in_pipeline_order)


def projected_mean_operational_occupancy_rate_normalized(
    trips_in_pipeline_order: Sequence[OperationalTrip],
    *,
    demand_curves: Mapping[int, Sequence[float]],
    ir_curves: Mapping[int, Sequence[float]],
    direction_starts: Mapping[int, int],
    vehicle_models: Mapping[int, VehicleModel],
    default_vehicle: VehicleModel,
    capacity_level: int,
) -> float:
    """Passenger-service-only projected occupancy, excluding express trips.

    Proposed modern indicator: ``taxa média de ocupação operacional projetada``.
    It is not a historical OferBus result and is intentionally reported separately
    from the overall projected occupancy rate.
    """
    normal_trips = [t for t in trips_in_pipeline_order if not t.is_express]
    if not normal_trips:
        raise ValueError("at least one normal passenger-service trip is required")

    occupancy_sum = 0.0
    directions = sorted({t.direction for t in normal_trips})
    for direction in directions:
        direction_trips = [t for t in normal_trips if t.direction == direction]
        previous = direction_trips[0].real_departure - 1
        for trip in direction_trips:
            passengers = passengers_in_period_legacy(
                demand_curves[direction],
                line_start=direction_starts[direction],
                start_real=previous + 1,
                end_real=trip.real_departure,
            )
            ir_idx = trip.real_departure - direction_starts[direction] + 1
            ir = float(ir_curves[direction][ir_idx])
            if ir == 0:
                raise ZeroDivisionError("operational projected occupancy rate divides by IR")
            vehicle = _trip_vehicle(trip, vehicle_models, default_vehicle)
            occupancy_sum += (passengers / ir) / _capacity(vehicle, capacity_level)
            previous = trip.real_departure

    return occupancy_sum / len(normal_trips)
