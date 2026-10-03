from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping


class SemanticLayer(StrEnum):
    LEGACY_EXACT = "legacy-exact"
    NORMALIZED = "normalized"
    MODERN = "modern"


@dataclass(frozen=True)
class ObservedTripInput:
    departure_service_minute: int
    passengers: int
    critical_passengers: int = 0
    travel_time_min: int = 0


@dataclass(frozen=True)
class DirectionPlanningInput:
    direction_key: str
    legacy_direction_number: int
    observations: tuple[ObservedTripInput, ...]
    demand_passengers_per_minute: tuple[float, ...]
    renewal_index_curve: tuple[float, ...]
    travel_time_min_curve: tuple[float, ...]
    service_start_minute: int
    service_end_minute: int
    demand_maximum_passengers_per_minute: float
    extension_km: float
    storage_at_departure_terminal: bool

    @property
    def service_minutes(self) -> int:
        return self.service_end_minute - self.service_start_minute + 1


@dataclass(frozen=True)
class VehiclePlanningInput:
    seats: int
    free_area_m2: float
    capacity_level: int = 1


@dataclass(frozen=True)
class CostPlanningInput:
    mode: str = "per_km"
    cost_per_km: float = 0.0
    fixed_cost_per_vehicle: float = 0.0
    variable_cost_per_km: float = 0.0


@dataclass(frozen=True)
class PlanningSpecification:
    max_headway_min: int
    project_capacity_passengers: float
    valley_capacity_passengers: float
    boarding_seconds_per_passenger: float
    alighting_seconds_per_passenger: float
    radial: bool
    create_express_returns: bool = False
    mean_renewal_index: float = 1.0
    typical_day_participation: float = 1.0
    equivalent_passenger_index: float = 1.0


@dataclass(frozen=True)
class PlanningInput:
    semantic_layer: SemanticLayer
    directions: tuple[DirectionPlanningInput, ...]
    vehicle: VehiclePlanningInput
    cost: CostPlanningInput
    specification: PlanningSpecification


@dataclass(frozen=True)
class PlannedTripResult:
    direction_key: str
    legacy_direction_number: int
    departure_service_minute: int
    arrival_service_minute: int
    virtual_departure_service_minute: int
    virtual_arrival_service_minute: int
    trip_type: int
    is_express: bool
    vehicle_block: int
    service_level: int | None


@dataclass(frozen=True)
class PlanningMetricsResult:
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


@dataclass(frozen=True)
class PlanningResult:
    semantic_layer: SemanticLayer
    engine_id: str
    engine_version: str
    input_fingerprint: str
    output_fingerprint: str
    trips: tuple[PlannedTripResult, ...]
    effective_fleet: int
    vehicle_blocks: Mapping[int, tuple[int, ...]]
    metrics: PlanningMetricsResult
    provenance_notes: tuple[str, ...]
