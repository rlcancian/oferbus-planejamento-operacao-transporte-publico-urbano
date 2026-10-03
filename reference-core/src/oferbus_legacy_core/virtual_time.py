from .numeric import legacy_round_gt_half


def _clamp_with_delta(minute: int, start: int, end: int) -> tuple[int, int]:
    if minute < start:
        return start, minute - start
    if minute > end:
        return end, minute - end
    return minute, 0


def _effective_load(*, demand: float, maximum: float, ir: float, project_capacity: float, valley_capacity: float) -> float:
    if maximum <= 0:
        return project_capacity * ir
    if demand < maximum:
        return (project_capacity - (project_capacity - valley_capacity) * (maximum - demand) / maximum) * ir
    return project_capacity * ir


def virtual_departure_legacy(*, real_departure: int, start: int, end: int, demand_curve: list[float], ir_curve: list[float],
                             maximum: float, project_capacity: float, valley_capacity: float, boarding_seconds: float) -> int:
    minute, delta = _clamp_with_delta(real_departure, start, end)
    idx = minute - start + 1
    load = _effective_load(demand=demand_curve[idx], maximum=maximum, ir=ir_curve[idx],
                           project_capacity=project_capacity, valley_capacity=valley_capacity)
    boarding_minutes = legacy_round_gt_half(load * boarding_seconds / 60.0)
    return minute - boarding_minutes + delta


def virtual_arrival_legacy(*, real_departure: int, start: int, end: int, demand_curve: list[float], ir_curve: list[float],
                           travel_time_curve: list[float], maximum: float, project_capacity: float,
                           valley_capacity: float, alighting_seconds: float) -> int:
    minute, delta = _clamp_with_delta(real_departure, start, end)
    idx = minute - start + 1
    load = _effective_load(demand=demand_curve[idx], maximum=maximum, ir=ir_curve[idx],
                           project_capacity=project_capacity, valley_capacity=valley_capacity)
    alighting_minutes = legacy_round_gt_half(load * alighting_seconds / 60.0)
    return int(alighting_minutes + minute + travel_time_curve[idx] + delta)
