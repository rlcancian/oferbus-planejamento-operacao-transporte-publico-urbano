from __future__ import annotations

from .contracts import PlanningInput, SemanticLayer


def validate_planning_input(value: PlanningInput) -> None:
    if not value.directions:
        raise ValueError("planning input requires at least one direction")
    if value.semantic_layer is SemanticLayer.MODERN:
        raise NotImplementedError("modern semantic layer has no promoted planning engine yet")

    spec = value.specification
    if spec.max_headway_min <= 0:
        raise ValueError("max_headway_min must be positive")
    if spec.project_capacity_passengers <= 0:
        raise ValueError("project_capacity_passengers must be positive")
    if spec.valley_capacity_passengers <= 0:
        raise ValueError("valley_capacity_passengers must be positive")
    if spec.valley_capacity_passengers > spec.project_capacity_passengers:
        raise ValueError("valley capacity cannot exceed project capacity")
    if spec.boarding_seconds_per_passenger < 0 or spec.alighting_seconds_per_passenger < 0:
        raise ValueError("boarding/alighting seconds cannot be negative")
    if spec.mean_renewal_index <= 0:
        raise ValueError("mean_renewal_index must be positive")
    if spec.typical_day_participation <= 0:
        raise ValueError("typical_day_participation must be positive")
    if spec.equivalent_passenger_index <= 0:
        raise ValueError("equivalent_passenger_index must be positive")

    vehicle = value.vehicle
    if vehicle.seats < 0:
        raise ValueError("vehicle seats cannot be negative")
    if vehicle.free_area_m2 <= 0:
        raise ValueError("vehicle free_area_m2 must be positive")
    if vehicle.capacity_level < 0:
        raise ValueError("vehicle capacity_level cannot be negative")

    if value.cost.mode not in {"per_km", "fixed_variable"}:
        raise ValueError("unsupported cost mode")
    if min(value.cost.cost_per_km, value.cost.fixed_cost_per_vehicle, value.cost.variable_cost_per_km) < 0:
        raise ValueError("cost parameters cannot be negative")

    direction_numbers: set[int] = set()
    direction_keys: set[str] = set()
    for direction in value.directions:
        if not direction.direction_key.strip():
            raise ValueError("direction_key cannot be blank")
        if direction.direction_key in direction_keys:
            raise ValueError(f"duplicate direction_key: {direction.direction_key}")
        if direction.legacy_direction_number in direction_numbers:
            raise ValueError(f"duplicate legacy_direction_number: {direction.legacy_direction_number}")
        if direction.legacy_direction_number <= 0:
            raise ValueError("legacy_direction_number must be positive")
        direction_keys.add(direction.direction_key)
        direction_numbers.add(direction.legacy_direction_number)

        if direction.service_end_minute < direction.service_start_minute:
            raise ValueError(f"direction {direction.direction_key} has an invalid service window")
        if direction.extension_km <= 0:
            raise ValueError(f"direction {direction.direction_key} extension_km must be positive")
        if direction.demand_maximum_passengers_per_minute < 0:
            raise ValueError(f"direction {direction.direction_key} demand maximum cannot be negative")
        if not direction.observations:
            raise ValueError(f"direction {direction.direction_key} requires observations")

        observation_minutes = [item.departure_service_minute for item in direction.observations]
        if observation_minutes != sorted(observation_minutes):
            raise ValueError(f"direction {direction.direction_key} observations must be sorted")
        if len(set(observation_minutes)) != len(observation_minutes):
            raise ValueError(f"direction {direction.direction_key} has duplicate observation departure minutes")
        if observation_minutes[0] < direction.service_start_minute or observation_minutes[-1] > direction.service_end_minute:
            raise ValueError(f"direction {direction.direction_key} observations are outside the service window")
        for observation in direction.observations:
            if observation.passengers < 0 or observation.critical_passengers < 0:
                raise ValueError("observed passengers cannot be negative")
            if observation.travel_time_min < 0:
                raise ValueError("observed travel time cannot be negative")

        minimum_curve_length = direction.service_minutes + 2
        curves = {
            "demand": direction.demand_passengers_per_minute,
            "renewal index": direction.renewal_index_curve,
            "travel time": direction.travel_time_min_curve,
        }
        for name, curve in curves.items():
            if len(curve) < minimum_curve_length:
                raise ValueError(
                    f"direction {direction.direction_key} {name} curve requires at least {minimum_curve_length} values"
                )
        if any(item < 0 for item in direction.demand_passengers_per_minute):
            raise ValueError("demand curve cannot contain negative values")
        if any(item <= 0 for item in direction.renewal_index_curve[1 : direction.service_minutes + 1]):
            raise ValueError("renewal index curve must be positive inside the service window")
        if any(item <= 0 for item in direction.travel_time_min_curve[1 : direction.service_minutes + 1]):
            raise ValueError("travel time curve must be positive inside the service window")
