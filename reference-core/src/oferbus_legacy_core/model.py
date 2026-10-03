from dataclasses import dataclass

@dataclass(frozen=True)
class TripObservation:
    minute: int
    passengers: int
    critical_passengers: int = 0
    travel_time: int = 0

@dataclass(frozen=True)
class VehicleModel:
    seats: int
    free_area_m2: float
