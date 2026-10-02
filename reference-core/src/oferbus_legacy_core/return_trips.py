from __future__ import annotations
from typing import Mapping

from .operations import LinkKind, OperationalTrip
from .timetable import DirectionPlanningData, MinimumTimetableConfig, PlannedTrip
from .trip_attributes import ExpressTravelParameters, complete_trip_attributes_legacy
from .virtual_time import virtual_arrival_legacy, virtual_departure_legacy


def _vdep(d: DirectionPlanningData, minute: int, cfg: MinimumTimetableConfig) -> int:
    return virtual_departure_legacy(
        real_departure=minute,
        start=d.start,
        end=d.end,
        demand_curve=list(d.demand_curve),
        ir_curve=list(d.ir_curve),
        maximum=d.maximum,
        project_capacity=cfg.project_capacity,
        valley_capacity=cfg.valley_capacity,
        boarding_seconds=cfg.boarding_seconds,
    )


def _varr(d: DirectionPlanningData, minute: int, cfg: MinimumTimetableConfig) -> int:
    return virtual_arrival_legacy(
        real_departure=minute,
        start=d.start,
        end=d.end,
        demand_curve=list(d.demand_curve),
        ir_curve=list(d.ir_curve),
        travel_time_curve=list(d.travel_time_curve),
        maximum=d.maximum,
        project_capacity=cfg.project_capacity,
        valley_capacity=cfg.valley_capacity,
        alighting_seconds=cfg.alighting_seconds,
    )


def create_return_trips_cria_1_legacy(
    trips: list[OperationalTrip],
    *,
    directions: Mapping[int, DirectionPlanningData],
    config: MinimumTimetableConfig,
    express_parameters: Mapping[int, ExpressTravelParameters] | None = None,
    line_number: int = 0,
    preserve_normal_return_type_bug: bool = True,
    max_trips: int = 400,
) -> int:
    """Reconstruct only ``MMARCHA1.Cria_1``.

    Preconditions from the historical caller are preserved: radial two-direction
    semantics, virtual-time ordering, and prior direct-linking attempt. The source
    inconsistency ``Tipo = 0 'TODO: 2`` is exposed as an explicit switch rather
    than silently corrected.
    """
    if not trips:
        return 0
    express_parameters = express_parameters or {}
    original_count = len(trips)
    created = 0

    for i in range(original_count):
        current = trips[i]
        if current.exit_link != LinkKind.NONE:
            continue

        direction = current.direction
        opposite = 3 - direction
        if opposite not in directions:
            raise KeyError(f"Cria_1 requires opposite direction {opposite}")
        od = directions[opposite]
        arrival = current.virtual_arrival

        if config.create_express_returns:
            if opposite not in express_parameters:
                raise KeyError(f"express parameters missing for direction {opposite}")
            pexp = express_parameters[opposite]
            idx = min(max(arrival - od.start + 1, 1), od.total_minutes)
            residual = od.travel_time_curve[idx] - pexp.base_express_minutes
            earliest_return_arrival = (
                arrival + 1 + pexp.base_express_minutes
                + residual * pexp.residual_percent / 100.0
            )
        else:
            minute = arrival
            while _vdep(od, minute, config) <= arrival:
                minute += 1
            earliest_return_arrival = _varr(od, minute, config)

        first_linked_other: int | None = None
        for j, candidate in enumerate(trips):
            if (
                candidate.virtual_departure > current.virtual_arrival
                and candidate.direction == opposite
                and candidate.entry_link == LinkKind.TRIP
            ):
                first_linked_other = j
                break

        limit_index = len(trips) - 1 if first_linked_other is None else first_linked_other
        if limit_index < len(trips) - 1:
            limit = trips[limit_index].virtual_arrival
        else:
            limit = trips[limit_index].virtual_departure

        target_index: int | None = None
        for k in range(i, len(trips)):
            candidate = trips[k]
            if (
                candidate.virtual_departure > earliest_return_arrival
                and candidate.virtual_departure <= limit
                and candidate.direction == direction
                and candidate.entry_link == LinkKind.NONE
            ):
                target_index = k
                break
        if target_index is None:
            continue
        if len(trips) >= max_trips:
            break

        target = trips[target_index]
        current.exit_link = LinkKind.TRIP
        target.entry_link = LinkKind.TRIP

        first_minute = current.virtual_arrival + 1
        if config.create_express_returns:
            departure = first_minute
            trip_type = 3
        else:
            q = first_minute
            while _varr(od, q, config) < target.virtual_departure:
                q += 1
            q -= 1
            midpoint = (first_minute + _vdep(od, q, config)) // 2
            departure = first_minute
            while _vdep(od, departure, config) < midpoint:
                departure += 1
            trip_type = 0 if preserve_normal_return_type_bug else 2

        new_trip = complete_trip_attributes_legacy(
            [PlannedTrip(opposite, departure, 0, trip_type)],
            directions=directions,
            config=config,
            line_number=line_number,
            express_parameters=express_parameters,
        )[0]
        new_trip.entry_link = LinkKind.TRIP
        new_trip.exit_link = LinkKind.TRIP
        trips.append(new_trip)
        created += 1

    if created:
        trips.sort(key=lambda t: t.virtual_departure)
    return created
