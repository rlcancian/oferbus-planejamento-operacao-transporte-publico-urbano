from .model import VehicleModel
from .numeric import legacy_round_gt_half


def capacity_levels_legacy(default_vehicle: VehicleModel, requested_vehicle: VehicleModel | None = None) -> list[float]:
    """Reproduces BUG-CAND-001: levels are always computed from gVeiculoPadrao."""
    return [default_vehicle.seats + 1.5 * default_vehicle.free_area_m2 * i for i in range(6)]


def capacity_levels_corrected(vehicle: VehicleModel) -> list[float]:
    """Scientifically/structurally corrected alternative; not legacy-compatible."""
    return [vehicle.seats + 1.5 * vehicle.free_area_m2 * i for i in range(6)]


def fleet_reserve_legacy(effective_fleet: int, reserve_percent: float) -> int:
    return legacy_round_gt_half(effective_fleet * reserve_percent / 100.0)
