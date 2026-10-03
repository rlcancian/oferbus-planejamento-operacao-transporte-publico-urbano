from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping

from .model import TripObservation
from .virtual_time import virtual_arrival_legacy, virtual_departure_legacy


@dataclass
class PlannedTrip:
    direction: int
    real_departure: int
    virtual_arrival: int
    trip_type: int = 0  # 0 normal; 2 return normal; 3 return express in the recovered procedure


@dataclass(frozen=True)
class DirectionPlanningData:
    observed: tuple[TripObservation, ...]
    demand_curve: tuple[float, ...]
    ir_curve: tuple[float, ...]
    travel_time_curve: tuple[float, ...]
    start: int
    end: int
    maximum: float
    storage_at_departure_terminal: bool

    @property
    def total_minutes(self) -> int:
        return self.end - self.start + 1


@dataclass(frozen=True)
class MinimumTimetableConfig:
    max_interval: int
    project_capacity: float
    valley_capacity: float
    boarding_seconds: float
    alighting_seconds: float
    radial: bool = True
    create_express_returns: bool = False
    max_trips: int = 400
    preserve_return_replay_bug: bool = True


def _arrival(d: DirectionPlanningData, departure: int, cfg: MinimumTimetableConfig) -> int:
    return virtual_arrival_legacy(
        real_departure=departure, start=d.start, end=d.end,
        demand_curve=list(d.demand_curve), ir_curve=list(d.ir_curve), travel_time_curve=list(d.travel_time_curve),
        maximum=d.maximum, project_capacity=cfg.project_capacity, valley_capacity=cfg.valley_capacity,
        alighting_seconds=cfg.alighting_seconds,
    )


def _virtual_departure(d: DirectionPlanningData, departure: int, cfg: MinimumTimetableConfig) -> int:
    return virtual_departure_legacy(
        real_departure=departure, start=d.start, end=d.end,
        demand_curve=list(d.demand_curve), ir_curve=list(d.ir_curve), maximum=d.maximum,
        project_capacity=cfg.project_capacity, valley_capacity=cfg.valley_capacity,
        boarding_seconds=cfg.boarding_seconds,
    )


def _effective_capacity(d: DirectionPlanningData, idx: int, cfg: MinimumTimetableConfig) -> float:
    demand = d.demand_curve[idx]
    ir = d.ir_curve[idx]
    if demand < d.maximum and d.maximum > 0:
        level = cfg.project_capacity - (cfg.project_capacity - cfg.valley_capacity) * (d.maximum - demand) / d.maximum
    else:
        level = cfg.project_capacity
    return level * ir


def _regularize_last_departures_legacy(trips: list[PlannedTrip], last_created: list[int]) -> None:
    """Port of the final 'bonitinhos' regularization block in the 2007 procedure.

    Index 0 in ``trips`` is a zero-valued dummy, reproducing the fixed-array
    behavior when fewer than five indices have been stored.
    """
    a, b, c, d, e = [trips[i].real_departure for i in last_created[:5]]
    if (a - b) < (b - c):
        if (b - c) <= (c - d):
            if (c - d) <= (d - e):
                step = int((a - e) / 4)
                trips[last_created[3]].real_departure = e + step
                trips[last_created[2]].real_departure = e + 2 * step
                trips[last_created[1]].real_departure = e + 3 * step
            else:
                # The legacy comment says '3 viagens' but the source divides by 4.
                step = int((a - d) / 4)
                trips[last_created[2]].real_departure = d + 2 * step
                trips[last_created[1]].real_departure = d + 3 * step
        else:
            trips[last_created[1]].real_departure = int((a + c) / 2)


def minimum_timetable_2007_legacy(
    directions: Mapping[int, DirectionPlanningData], cfg: MinimumTimetableConfig,
) -> list[PlannedTrip]:
    """Direct reconstruction of ``MMARCHA1.Calcula_Quadro_Horarios_Minimo_2007``.

    This is intentionally a characterization engine, not a redesigned scheduler.
    It preserves return-trip types and can preserve the known passenger-replay
    indexing defect via ``preserve_return_replay_bug``.  The subsequent
    ``Ajeitadinha_Brasileira_Horarios``, full attribute completion, graph linking,
    and fleet allocation remain separate legacy stages.
    """
    if not directions:
        return []
    for direction, data in directions.items():
        if not data.observed:
            raise ValueError(f"direction {direction} has no observations")
        if len(data.demand_curve) < data.total_minutes + 2:
            raise ValueError(f"direction {direction} demand curve is too short")

    direction_count = max(directions)
    if cfg.radial and direction_count >= 2 and not directions[1].storage_at_departure_terminal:
        order = list(range(direction_count, 0, -1))
    else:
        order = list(range(1, direction_count + 1))

    # Dummy index 0 reproduces VB fixed arrays whose zero element is default-initialized.
    trips: list[PlannedTrip] = [PlannedTrip(0, 0, 0, 0)]

    for direction in order:
        d = directions[direction]
        last_created = [0, 0, 0, 0, 0]
        last_normal = 0
        passenger_sum = 0.0
        must_return = False
        has_vehicle_here = False
        last_arriving = 0
        penultimate_arriving = 0
        next_arriving = 0

        first_obs = d.observed[0].minute
        if first_obs == d.start or d.storage_at_departure_terminal:
            trips.append(PlannedTrip(direction, first_obs, _arrival(d, first_obs, cfg), 0))
            last_created[0] = len(trips) - 1
            last_normal = last_created[0]
            cont = 1 if first_obs == d.start else first_obs - d.start + 1
        else:
            cont = 0

        if not d.storage_at_departure_terminal:
            current_abs = cont + d.start  # cont not yet incremented; source adds -1+1
            candidates = [i for i in range(1, len(trips)) if trips[i].direction == 3 - direction and trips[i].virtual_arrival < current_abs]
            last_arriving = candidates[-1] if candidates else 0
            future = [i for i in range(1, len(trips)) if trips[i].direction == 3 - direction and trips[i].virtual_arrival > (cont + d.start - 1)]
            if not future:
                raise ValueError("legacy invariant violated: no opposite-direction trip available to arrive")
            next_arriving = future[0]

        while cont < d.total_minutes:
            continues = True
            effective_capacity = cfg.project_capacity
            interval = 0
            while continues and cont < d.total_minutes and not must_return:
                cont += 1
                idx = cont
                effective_capacity = _effective_capacity(d, idx, cfg)
                passenger_sum += d.demand_curve[idx]
                continues = passenger_sum < effective_capacity

                if last_normal > 0:
                    interval = cont - (trips[last_normal].real_departure - d.start + 1)
                else:
                    abs_minute = cont + d.start - 1
                    threshold = first_obs - cfg.max_interval
                    interval = 0 if abs_minute < threshold else abs_minute - threshold
                continues = continues and (interval < cfg.max_interval)

                if not d.storage_at_departure_terminal:
                    abs_minute = cont + d.start - 1
                    if abs_minute == trips[next_arriving].virtual_arrival:
                        if continues:
                            if has_vehicle_here:
                                must_return = True
                            else:
                                has_vehicle_here = True
                        else:
                            must_return = False
                            has_vehicle_here = True
                        penultimate_arriving = last_arriving
                        last_arriving = next_arriving
                        future = [i for i in range(next_arriving + 1, len(trips)) if trips[i].direction == 3 - direction and trips[i].virtual_arrival > abs_minute]
                        if future:
                            next_arriving = future[0]

            if passenger_sum > effective_capacity:
                passenger_sum -= d.demand_curve[cont]
                cont -= 1

            if len(trips) - 1 >= cfg.max_trips:
                break

            if (not continues) or d.storage_at_departure_terminal:
                departure = cont + d.start - 1
                trips.append(PlannedTrip(direction, departure, _arrival(d, departure, cfg), 0))
                idx_new = len(trips) - 1
                passenger_sum = 0.0
                if last_arriving > 0 and not d.storage_at_departure_terminal:
                    if trips[last_arriving].virtual_arrival < _virtual_departure(d, departure, cfg):
                        has_vehicle_here = False
                else:
                    has_vehicle_here = False
                last_normal = idx_new
            else:
                if last_created[0] > 0:
                    departure = (trips[last_created[0]].real_departure + cont + d.start - 1) // 2
                else:
                    departure = (d.start + cont + d.start - 1) // 2
                if penultimate_arriving > 0 and departure <= trips[penultimate_arriving].virtual_arrival:
                    departure = trips[penultimate_arriving].virtual_arrival + 1
                while penultimate_arriving > 0 and _virtual_departure(d, departure, cfg) < trips[penultimate_arriving].virtual_arrival + 1:
                    departure += 1
                trip_type = 3 if cfg.create_express_returns else 2
                trips.append(PlannedTrip(direction, departure, _arrival(d, departure, cfg), trip_type))
                idx_new = len(trips) - 1
                if not cfg.create_express_returns:
                    passenger_sum = 0.0
                    replay_end_abs = cont + d.start - 1
                    for absolute_minute in range(departure + 1, replay_end_abs + 1):
                        if cfg.preserve_return_replay_bug:
                            # Source uses CurvaAjustada(sent, cont), not CurvaAjustada(sent, i).
                            replay_idx = cont
                        else:
                            replay_idx = absolute_minute - d.start + 1
                        if 1 <= replay_idx <= d.total_minutes:
                            passenger_sum += d.demand_curve[replay_idx]
                    last_normal = idx_new
                must_return = False

            last_created = [idx_new, *last_created[:4]]

        if trips[-1].direction == direction and trips[-1].real_departure < d.observed[-1].minute and len(trips) - 1 < cfg.max_trips:
            dep = d.observed[-1].minute
            trips.append(PlannedTrip(direction, dep, _arrival(d, dep, cfg), 0))
            last_created = [len(trips) - 1, *last_created[:4]]

        _regularize_last_departures_legacy(trips, last_created)
        for idx in last_created:
            if idx > 0:
                trips[idx].virtual_arrival = _arrival(d, trips[idx].real_departure, cfg)

    return trips[1:]
