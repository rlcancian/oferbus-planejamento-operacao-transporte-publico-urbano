from __future__ import annotations

from typing import Mapping

from .operations import LinkKind, OperationalTrip
from .return_trips import _vdep, _varr
from .timetable import DirectionPlanningData, MinimumTimetableConfig, PlannedTrip
from .trip_attributes import ExpressTravelParameters, complete_trip_attributes_legacy


def create_return_trips_cria_2_storage_branch_legacy(
    trips: list[OperationalTrip],
    *,
    directions: Mapping[int, DirectionPlanningData],
    config: MinimumTimetableConfig,
    express_parameters: Mapping[int, ExpressTravelParameters] | None = None,
    line_number: int = 0,
    max_trips: int = 400,
) -> int:
    """Characterization reconstruction of the storage-enabled branch of ``Cria_2``.

    ``Cria_2`` inserts a return trip when an unresolved arrival could be connected
    to a later same-direction departure only by creating an opposite-direction
    movement in between. This function reconstructs the branch for which the
    legacy ``AreaEstocagem(Sent)`` flag is true. Both documented start-interval
    cases are covered: when the backward opposite-direction anchor exists its
    departure is used; otherwise the interval starts one minute after the current
    arrival. The later no-storage branch remains explicitly separate because the
    active 2008 source contains additional indexing/direction inconsistencies.
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
        if direction not in directions or opposite not in directions:
            continue
        d_current = directions[direction]
        d_opposite = directions[opposite]
        if not d_current.storage_at_departure_terminal:
            continue

        j = current.virtual_arrival
        if config.create_express_returns:
            params = express_parameters.get(opposite)
            if params is None:
                raise KeyError(f"express parameters missing for direction {opposite}")
            idx = min(max(j - d_opposite.start + 1, 1), d_opposite.total_minutes)
            residual = d_opposite.travel_time_curve[idx] - params.base_express_minutes
            earliest_arrival = j + 1 + params.base_express_minutes + residual * params.residual_percent / 100.0
        else:
            minute = j + 1
            while _vdep(d_opposite, minute, config) < j + 1:
                minute += 1
            earliest_arrival = _varr(d_opposite, minute, config)

        target_index: int | None = None
        for k in range(i, len(trips)):
            candidate = trips[k]
            if (
                candidate.virtual_departure > earliest_arrival
                and candidate.direction == direction
                and candidate.entry_link == LinkKind.NONE
            ):
                target_index = k
                break
        if target_index is None:
            continue
        target = trips[target_index]

        n_index: int | None = None
        for n in range(i, len(trips)):
            candidate = trips[n]
            if candidate.virtual_departure >= target.virtual_departure:
                break
            if (
                candidate.direction == opposite
                and candidate.virtual_arrival < target.virtual_departure
                and candidate.virtual_departure > j
            ):
                n_index = n
                break
        if n_index is None:
            continue

        p_index: int | None = None
        for p in range(n_index, -1, -1):
            candidate = trips[p]
            if (
                candidate.direction == opposite
                and candidate.virtual_arrival <= earliest_arrival
                and candidate.virtual_departure <= j
            ):
                p_index = p
                break
        if len(trips) >= max_trips:
            break
        start_interval = trips[p_index].virtual_departure if p_index is not None else j + 1
        end_interval = trips[n_index].virtual_departure

        if config.create_express_returns:
            departure = j + 1
            trip_type = 3
        else:
            departure = start_interval + (end_interval - start_interval) // 2
            fixed_virtual = departure
            while _vdep(d_opposite, departure, config) < fixed_virtual:
                departure += 1
            while _vdep(d_opposite, departure, config) <= j:
                departure += 1
            trip_type = 2

        new_trip = complete_trip_attributes_legacy(
            [PlannedTrip(opposite, departure, 0, trip_type)],
            directions=directions,
            config=config,
            line_number=line_number,
            express_parameters=express_parameters,
        )[0]

        current.exit_link = LinkKind.TRIP
        new_trip.entry_link = LinkKind.TRIP
        new_trip.exit_link = LinkKind.STORAGE
        target.entry_link = LinkKind.STORAGE
        trips.append(new_trip)
        created += 1

    if created:
        trips.sort(key=lambda t: t.virtual_departure)
    return created


def create_return_trips_cria_2_no_storage_anchored_branch_legacy(
    trips: list[OperationalTrip],
    *,
    directions: Mapping[int, DirectionPlanningData],
    config: MinimumTimetableConfig,
    express_parameters: Mapping[int, ExpressTravelParameters] | None = None,
    line_number: int = 0,
    max_trips: int = 400,
) -> int:
    """Reconstruct the fully anchored no-storage branch of ``Cria_2``.

    This covers the 2008c path in which all three temporal anchors used by the
    source are present: a previous opposite-direction trip, a later opposite-
    direction trip, and a previous same-direction departure before the target.

    The source fallbacks used when any of these anchors is absent are deliberately
    excluded. One fallback calls ``Calc_ChegadaVirtual(Sent, ...)`` while creating
    an ``outroSent`` trip, and the backward scan has an unsafe bound. Those paths
    are recorded as BC-012 rather than silently normalized here.
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
        if direction not in directions or opposite not in directions:
            continue
        d_current = directions[direction]
        d_opposite = directions[opposite]
        if d_current.storage_at_departure_terminal:
            continue

        j = current.virtual_arrival
        if config.create_express_returns:
            params = express_parameters.get(opposite)
            if params is None:
                raise KeyError(f"express parameters missing for direction {opposite}")
            idx = min(max(j - d_opposite.start + 1, 1), d_opposite.total_minutes)
            residual = d_opposite.travel_time_curve[idx] - params.base_express_minutes
            earliest_arrival = j + 1 + params.base_express_minutes + residual * params.residual_percent / 100.0
        else:
            minute = j + 1
            while _vdep(d_opposite, minute, config) < j + 1:
                minute += 1
            earliest_arrival = _varr(d_opposite, minute, config)

        target_index: int | None = None
        for k in range(i, len(trips)):
            candidate = trips[k]
            if (
                candidate.virtual_departure > earliest_arrival
                and candidate.direction == direction
                and candidate.entry_link == LinkKind.NONE
            ):
                target_index = k
                break
        if target_index is None:
            continue
        target = trips[target_index]

        previous_opposite: int | None = None
        for n in range(target_index, -1, -1):
            candidate = trips[n]
            if candidate.direction == opposite and candidate.virtual_arrival < target.virtual_departure:
                previous_opposite = n
                break
        if previous_opposite is None:
            continue
        start_interval = trips[previous_opposite].virtual_departure

        next_opposite: int | None = None
        for p in range(previous_opposite, len(trips)):
            candidate = trips[p]
            if candidate.direction == opposite and candidate.virtual_arrival >= target.virtual_departure:
                next_opposite = p
                break
        if next_opposite is None:
            continue
        end_interval = trips[next_opposite].virtual_departure - 1

        previous_same: int | None = None
        for m in range(target_index - 1, -1, -1):
            candidate = trips[m]
            if candidate.direction == direction and candidate.virtual_departure < target.virtual_departure:
                previous_same = m
                break
        if previous_same is None:
            continue

        if len(trips) >= max_trips:
            break

        if config.create_express_returns:
            params = express_parameters.get(opposite)
            if params is None:
                raise KeyError(f"express parameters missing for direction {opposite}")
            departure = end_interval
            midpoint = (trips[previous_same].virtual_departure + target.virtual_departure) // 2
            while True:
                idx = min(max(departure - d_opposite.start + 1, 1), d_opposite.total_minutes)
                residual = d_opposite.travel_time_curve[idx] - params.base_express_minutes
                arrival = departure + params.base_express_minutes + residual * params.residual_percent / 100.0
                departure += 1
                if arrival >= midpoint:
                    break
            departure -= 1
            trip_type = 3
        else:
            departure = start_interval + (end_interval - start_interval) // 2
            while _varr(d_opposite, departure, config) < trips[previous_same].virtual_departure:
                departure += 1
            while _varr(d_opposite, departure, config) >= target.virtual_departure:
                departure -= 1
            trip_type = 2

        new_trip = complete_trip_attributes_legacy(
            [PlannedTrip(opposite, departure, 0, trip_type)],
            directions=directions,
            config=config,
            line_number=line_number,
            express_parameters=express_parameters,
        )[0]

        r_index: int | None = None
        for r in range(previous_opposite, len(trips)):
            candidate = trips[r]
            if candidate.direction == opposite and candidate.virtual_departure > departure:
                r_index = r
                break

        direct_entry_for_new = False
        if r_index is not None:
            interfering_arrival = any(
                candidate.direction == direction
                and candidate.virtual_arrival >= departure
                and candidate.virtual_arrival < trips[r_index].virtual_departure
                for candidate in trips[: target_index + 1]
            )
            if not interfering_arrival:
                trips[r_index].entry_link = LinkKind.STORAGE
                direct_entry_for_new = True

        current.exit_link = LinkKind.STORAGE
        new_trip.entry_link = LinkKind.TRIP if direct_entry_for_new else LinkKind.STORAGE
        new_trip.exit_link = LinkKind.TRIP
        target.entry_link = LinkKind.TRIP
        trips.append(new_trip)
        created += 1

    if created:
        trips.sort(key=lambda t: t.virtual_departure)
    return created
