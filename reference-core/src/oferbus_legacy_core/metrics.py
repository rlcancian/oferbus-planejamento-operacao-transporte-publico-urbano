from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .model import TripObservation, VehicleModel
from .operations import OperationalTrip
from .service_level import passengers_in_period_legacy


@dataclass(frozen=True)
class CostParameters:
    """Recovered OferBus line-operating cost parameters.

    ``mode='per_km'`` reproduces ``TipoCusto=0``.
    ``mode='fixed_variable'`` reproduces the fixed + variable branch.
    """

    mode: str
    cost_per_km: float = 0.0
    fixed_cost_per_vehicle: float = 0.0
    variable_cost_per_km: float = 0.0


@dataclass(frozen=True)
class OccupancyExtreme:
    maximum_passengers: int
    maximum_passengers_departure: int | None
    maximum_critical_density: float
    maximum_critical_density_departure: int | None


@dataclass(frozen=True)
class OperatingMetrics:
    total_passengers: int
    total_trips: int
    mean_extension_km: float
    total_distance_km: float
    effective_fleet: int
    mean_daily_distance_per_vehicle_km: float
    mean_passengers_per_trip: float
    mean_critical_passengers_per_trip: float
    mean_occupancy_rate: float | None
    passengers_per_km: float
    daily_total_cost: float
    mean_cost_per_vehicle: float
    cost_per_trip: float
    cost_per_equivalent_passenger: float
    mean_trips_per_vehicle: float
    mean_travel_time_min: float
    mean_speed_kmh: float
    distance_semantics: str


def monthly_cost_legacy(daily_cost: float, typical_day: int) -> float:
    """Exact ``Calcula_Custo_Mensal`` conversion used by the legacy code."""
    days_per_week = {0: 4.8358, 1: 0.9671, 2: 1.1971}
    if typical_day not in days_per_week:
        raise ValueError("typical_day must be 0, 1, or 2")
    weeks_per_month = 365.25 / 12.0 / 7.0
    return float(daily_cost) * weeks_per_month * days_per_week[typical_day]


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


def projected_worst_occupancy_legacy(
    trips: Sequence[OperationalTrip],
    *,
    demand_curves: Mapping[int, Sequence[float]],
    ir_curves: Mapping[int, Sequence[float]],
    direction_starts: Mapping[int, int],
    vehicle_models: Mapping[int, VehicleModel],
    default_vehicle: VehicleModel,
) -> OccupancyExtreme:
    """Port of ``Calcula_Pior_Ocupacao_Projetada``.

    Express trips transport zero passengers in this procedure and do not move the
    previous-normal-trip marker. Critical occupancy is converted to standing
    density (passengers/m²) after subtracting seats.
    """
    ordered = sorted(trips, key=lambda t: t.real_departure)
    last_normal_departure: dict[int, int] = {}
    max_passengers = 0
    max_passenger_time: int | None = None
    max_density = 0.0
    max_density_time: int | None = None

    for trip in ordered:
        direction = trip.direction
        if trip.is_express:
            passengers = 0
        elif direction in last_normal_departure:
            passengers = passengers_in_period_legacy(
                demand_curves[direction],
                line_start=direction_starts[direction],
                start_real=last_normal_departure[direction] + 1,
                end_real=trip.real_departure,
            )
        else:
            passengers = passengers_in_period_legacy(
                demand_curves[direction],
                line_start=direction_starts[direction],
                start_real=trip.real_departure,
                end_real=trip.real_departure,
            )

        if not trip.is_express:
            last_normal_departure[direction] = trip.real_departure

        if passengers > max_passengers:
            max_passengers = passengers
            max_passenger_time = trip.real_departure

        ir_idx = trip.real_departure - direction_starts[direction] + 1
        ir = float(ir_curves[direction][ir_idx])
        if ir == 0:
            raise ZeroDivisionError("legacy projected occupancy divides by IR")
        critical_passengers = passengers / ir
        vehicle = _trip_vehicle(trip, vehicle_models, default_vehicle)
        if vehicle.free_area_m2 <= 0:
            raise ValueError("vehicle free area must be positive")
        standing = max(critical_passengers - vehicle.seats, 0.0)
        density = standing / vehicle.free_area_m2
        if density > max_density:
            max_density = density
            max_density_time = trip.real_departure

    return OccupancyExtreme(
        max_passengers,
        max_passenger_time,
        max_density,
        max_density_time,
    )


def projected_mean_occupancy_rate_legacy(
    trips_in_pipeline_order: Sequence[OperationalTrip],
    *,
    demand_curves: Mapping[int, Sequence[float]],
    ir_curves: Mapping[int, Sequence[float]],
    direction_starts: Mapping[int, int],
    vehicle_models: Mapping[int, VehicleModel],
    default_vehicle: VehicleModel,
    capacity_level: int,
) -> float:
    """Exact structure of ``Calcula_Taxa_Ocupacao_Projetada``.

    Important legacy behavior: express trips are included, consume a demand
    interval, advance ``anterior`` and remain in the denominator. This conflicts
    with ``Calcula_Pior_Ocupacao_Projetada`` and is preserved for characterization.
    """
    if not trips_in_pipeline_order:
        raise ValueError("at least one projected trip is required")

    occupancy_sum = 0.0
    directions = sorted({t.direction for t in trips_in_pipeline_order})
    for direction in directions:
        direction_trips = [t for t in trips_in_pipeline_order if t.direction == direction]
        if not direction_trips:
            continue
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
                raise ZeroDivisionError("legacy projected occupancy rate divides by IR")
            critical = passengers / ir
            vehicle = _trip_vehicle(trip, vehicle_models, default_vehicle)
            occupancy_sum += critical / _capacity(vehicle, capacity_level)
            previous = trip.real_departure

    return occupancy_sum / len(trips_in_pipeline_order)


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
    """Comparison variant consistent with the legacy worst-occupancy express rule.

    Express trips transport zero passengers, do not advance the previous-normal
    marker and are excluded from the averaging denominator. This is not claimed to
    be historical behavior; it exists to expose BC-010 quantitatively.
    """
    normal_trips = [t for t in trips_in_pipeline_order if not t.is_express]
    if not normal_trips:
        raise ValueError("at least one normal trip is required")

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
                raise ZeroDivisionError("normalized projected occupancy rate divides by IR")
            vehicle = _trip_vehicle(trip, vehicle_models, default_vehicle)
            occupancy_sum += (passengers / ir) / _capacity(vehicle, capacity_level)
            previous = trip.real_departure

    return occupancy_sum / len(normal_trips)


def _daily_cost(
    distance_km: float,
    *,
    fleet: int,
    cost: CostParameters,
    typical_day_participation: float,
) -> float:
    if cost.mode == "per_km":
        return distance_km * cost.cost_per_km
    if cost.mode == "fixed_variable":
        return (
            distance_km * cost.variable_cost_per_km
            + fleet * typical_day_participation * cost.fixed_cost_per_vehicle
        )
    raise ValueError("unsupported cost mode")


def _assemble_metrics(
    *,
    total_passengers: int,
    trip_counts: Mapping[int, int],
    total_travel_time_min: float,
    extension_km_by_direction: Mapping[int, float],
    effective_fleet: int,
    mean_renewal_index: float,
    mean_occupancy_rate: float | None,
    cost: CostParameters,
    typical_day_participation: float,
    equivalent_passenger_index: float,
    corrected_distance: bool,
) -> OperatingMetrics:
    total_trips = sum(trip_counts.values())
    if total_trips <= 0:
        raise ValueError("total trips must be positive")
    if effective_fleet <= 0:
        raise ValueError("effective fleet must be positive")
    if total_passengers <= 0:
        raise ValueError("total passengers must be positive")
    if mean_renewal_index == 0:
        raise ZeroDivisionError("mean renewal index must be non-zero")
    if equivalent_passenger_index == 0:
        raise ZeroDivisionError("equivalent passenger index must be non-zero")
    if total_travel_time_min <= 0:
        raise ValueError("total travel time must be positive")

    directions = sorted(trip_counts)
    mean_extension = sum(extension_km_by_direction[d] for d in directions) / len(directions)
    if corrected_distance:
        total_distance = sum(trip_counts[d] * extension_km_by_direction[d] for d in directions)
        mean_speed = total_distance * 60.0 / total_travel_time_min
        semantics = "direction-weighted"
    else:
        total_distance = total_trips * mean_extension
        mean_trip_time = total_travel_time_min / total_trips
        mean_speed = mean_extension * 60.0 / mean_trip_time
        semantics = "legacy-total-trips-times-mean-extension"

    if total_distance <= 0:
        raise ValueError("total distance must be positive")

    daily_cost = _daily_cost(
        total_distance,
        fleet=effective_fleet,
        cost=cost,
        typical_day_participation=typical_day_participation,
    )
    mean_trip_time = total_travel_time_min / total_trips
    mean_occupancy = total_passengers / total_trips

    return OperatingMetrics(
        total_passengers=total_passengers,
        total_trips=total_trips,
        mean_extension_km=mean_extension,
        total_distance_km=total_distance,
        effective_fleet=effective_fleet,
        mean_daily_distance_per_vehicle_km=total_distance / effective_fleet,
        mean_passengers_per_trip=mean_occupancy,
        mean_critical_passengers_per_trip=mean_occupancy / mean_renewal_index,
        mean_occupancy_rate=mean_occupancy_rate,
        passengers_per_km=total_passengers / total_distance,
        daily_total_cost=daily_cost,
        mean_cost_per_vehicle=daily_cost / effective_fleet,
        cost_per_trip=daily_cost / total_trips,
        cost_per_equivalent_passenger=(daily_cost / total_passengers) / equivalent_passenger_index,
        mean_trips_per_vehicle=total_trips / effective_fleet,
        mean_travel_time_min=mean_trip_time,
        mean_speed_kmh=mean_speed,
        distance_semantics=semantics,
    )


def calculate_project_metrics_legacy(
    trips: Sequence[OperationalTrip],
    *,
    total_passengers_by_direction: Mapping[int, int],
    extension_km_by_direction: Mapping[int, float],
    effective_fleet: int,
    mean_renewal_index: float,
    mean_occupancy_rate: float,
    cost: CostParameters,
    typical_day_participation: float,
    equivalent_passenger_index: float,
) -> OperatingMetrics:
    """Port of ``Calcula_Inform_Resultados`` including the BC-005 distance formula."""
    trip_counts: dict[int, int] = {d: 0 for d in extension_km_by_direction}
    total_time = 0.0
    for trip in trips:
        trip_counts[trip.direction] = trip_counts.get(trip.direction, 0) + 1
        total_time += trip.real_arrival - trip.real_departure
    total_passengers = sum(total_passengers_by_direction.values())
    return _assemble_metrics(
        total_passengers=total_passengers,
        trip_counts=trip_counts,
        total_travel_time_min=total_time,
        extension_km_by_direction=extension_km_by_direction,
        effective_fleet=effective_fleet,
        mean_renewal_index=mean_renewal_index,
        mean_occupancy_rate=mean_occupancy_rate,
        cost=cost,
        typical_day_participation=typical_day_participation,
        equivalent_passenger_index=equivalent_passenger_index,
        corrected_distance=False,
    )


def calculate_project_metrics_distance_corrected(
    trips: Sequence[OperationalTrip],
    *,
    total_passengers_by_direction: Mapping[int, int],
    extension_km_by_direction: Mapping[int, float],
    effective_fleet: int,
    mean_renewal_index: float,
    mean_occupancy_rate: float,
    cost: CostParameters,
    typical_day_participation: float,
    equivalent_passenger_index: float,
) -> OperatingMetrics:
    """Comparison variant correcting only direction-weighted distance and speed."""
    trip_counts: dict[int, int] = {d: 0 for d in extension_km_by_direction}
    total_time = 0.0
    for trip in trips:
        trip_counts[trip.direction] = trip_counts.get(trip.direction, 0) + 1
        total_time += trip.real_arrival - trip.real_departure
    return _assemble_metrics(
        total_passengers=sum(total_passengers_by_direction.values()),
        trip_counts=trip_counts,
        total_travel_time_min=total_time,
        extension_km_by_direction=extension_km_by_direction,
        effective_fleet=effective_fleet,
        mean_renewal_index=mean_renewal_index,
        mean_occupancy_rate=mean_occupancy_rate,
        cost=cost,
        typical_day_participation=typical_day_participation,
        equivalent_passenger_index=equivalent_passenger_index,
        corrected_distance=True,
    )


def calculate_observed_metrics_legacy(
    observations_by_direction: Mapping[int, Sequence[TripObservation]],
    *,
    extension_km_by_direction: Mapping[int, float],
    available_fleet: int,
    mean_renewal_index: float,
    cost: CostParameters,
    typical_day_participation: float,
    equivalent_passenger_index: float,
) -> OperatingMetrics:
    """Port of ``Calcula_Inform_Levantamento`` for the observed baseline."""
    trip_counts = {d: len(observations_by_direction.get(d, ())) for d in extension_km_by_direction}
    total_passengers = sum(
        obs.passengers for values in observations_by_direction.values() for obs in values
    )
    positive_times = [
        obs.travel_time
        for values in observations_by_direction.values()
        for obs in values
        if obs.travel_time > 0
    ]
    if not positive_times:
        raise ValueError("observed metrics require at least one positive travel time")
    total_distance = sum(trip_counts[d] * extension_km_by_direction[d] for d in trip_counts)
    total_trips = sum(trip_counts.values())
    mean_extension = sum(extension_km_by_direction[d] for d in trip_counts) / len(trip_counts)
    mean_trip_time = sum(positive_times) / len(positive_times)
    if available_fleet <= 0:
        raise ValueError("available fleet must be positive")
    if total_passengers <= 0 or total_trips <= 0 or total_distance <= 0:
        raise ValueError("observed totals must be positive")
    if mean_renewal_index == 0 or equivalent_passenger_index == 0:
        raise ZeroDivisionError("IR and equivalent passenger index must be non-zero")
    daily_cost = _daily_cost(
        total_distance,
        fleet=available_fleet,
        cost=cost,
        typical_day_participation=typical_day_participation,
    )
    mean_occupancy = total_passengers / total_trips
    return OperatingMetrics(
        total_passengers=total_passengers,
        total_trips=total_trips,
        mean_extension_km=mean_extension,
        total_distance_km=total_distance,
        effective_fleet=available_fleet,
        mean_daily_distance_per_vehicle_km=total_distance / available_fleet,
        mean_passengers_per_trip=mean_occupancy,
        mean_critical_passengers_per_trip=mean_occupancy / mean_renewal_index,
        mean_occupancy_rate=None,
        passengers_per_km=total_passengers / total_distance,
        daily_total_cost=daily_cost,
        mean_cost_per_vehicle=daily_cost / available_fleet,
        cost_per_trip=daily_cost / total_trips,
        cost_per_equivalent_passenger=(daily_cost / total_passengers) / equivalent_passenger_index,
        mean_trips_per_vehicle=total_trips / available_fleet,
        mean_travel_time_min=mean_trip_time,
        mean_speed_kmh=mean_extension * 60.0 / mean_trip_time,
        distance_semantics="legacy-observed-direction-weighted",
    )
