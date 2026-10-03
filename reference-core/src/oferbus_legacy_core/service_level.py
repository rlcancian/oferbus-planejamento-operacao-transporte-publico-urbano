from __future__ import annotations
import math
from typing import Mapping, Sequence

from .model import VehicleModel
from .numeric import legacy_round_gt_half
from .operations import OperationalTrip


def service_level_label_legacy(critical_passengers: int, vehicle: VehicleModel) -> str:
    """Port of ``MGERAL.Get_NivelServico`` for an explicit vehicle model."""
    if vehicle.free_area_m2 <= 0:
        raise ValueError("vehicle free area must be positive")
    density = max(float(critical_passengers) - vehicle.seats, 0.0) / vehicle.free_area_m2
    if density == 0:
        return "A"
    bucket = math.floor(density / 1.5)
    if (density / 1.5) - math.floor(density / 1.5) > 0:
        bucket += 1
    if bucket <= 5:
        return chr(65 + int(bucket))
    return "F" + str(int(bucket) - 5)


def stored_service_level_legacy(critical_passengers: int, vehicle: VehicleModel) -> int:
    """Reproduce ``Asc(Get_NivelServico(...)) - 65``.

    Labels beyond F (``F1``, ``F2``, ...) collapse to integer level 5 because the
    caller reads only the first character through ``Asc``.
    """
    label = service_level_label_legacy(critical_passengers, vehicle)
    return ord(label[0]) - 65


def passengers_in_period_legacy(
    demand_curve: Sequence[float], *, line_start: int, start_real: int, end_real: int
) -> int:
    """Port of ``Calcula_Passageiros_No_Periodo`` for one direction."""
    total = 0.0
    for minute in range(start_real, end_real + 1):
        idx = minute - line_start + 1
        if 1 <= idx < len(demand_curve) - 1:
            total += demand_curve[idx]
    return legacy_round_gt_half(total)


def previous_normal_departure_legacy(
    trips_in_pipeline_order: Sequence[OperationalTrip], *, trip_index: int
) -> int:
    """Port of ``Acha_Viagem_Anterior`` as called after virtual-time ordering."""
    current = trips_in_pipeline_order[trip_index]
    previous_index: int | None = None
    for i, candidate in enumerate(trips_in_pipeline_order):
        if candidate.real_departure >= current.real_departure:
            break
        if candidate.direction == current.direction and not candidate.is_express:
            previous_index = i
    if previous_index is None or previous_index <= 0:
        return trips_in_pipeline_order[0].real_departure - 1
    return trips_in_pipeline_order[previous_index].real_departure


def assign_service_levels_legacy(
    trips_in_virtual_order: Sequence[OperationalTrip],
    *,
    demand_curves: Mapping[int, Sequence[float]],
    ir_curves: Mapping[int, Sequence[float]],
    direction_starts: Mapping[int, int],
    vehicle_models: Mapping[int, VehicleModel],
) -> None:
    """Reconstruct ``Define_NS_Viagens`` + ``Calcula_NS_Viagem``.

    ``vehicle_models`` is keyed by logical vehicle number. The legacy program looked
    up the vehicle restriction/model through global arrays; this API makes that
    dependency explicit.
    """
    for index, trip in enumerate(trips_in_virtual_order):
        if trip.is_express:
            trip.service_level = -1
            continue
        previous = previous_normal_departure_legacy(trips_in_virtual_order, trip_index=index)
        demand = passengers_in_period_legacy(
            demand_curves[trip.direction],
            line_start=direction_starts[trip.direction],
            start_real=previous + 1,
            end_real=trip.real_departure,
        )
        ir_idx = trip.real_departure - direction_starts[trip.direction] + 1
        ir = ir_curves[trip.direction][ir_idx]
        if ir == 0:
            raise ZeroDivisionError("legacy service-level calculation divides by IR")
        critical = math.floor(demand / ir)
        if trip.vehicle not in vehicle_models:
            raise KeyError(f"vehicle {trip.vehicle} has no model")
        trip.service_level = stored_service_level_legacy(critical, vehicle_models[trip.vehicle])
