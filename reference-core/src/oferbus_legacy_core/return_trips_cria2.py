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
    legacy ``AreaEstocagem(Sent)`` flag is true and for which the source finds the
    backward anchor used to define the creation interval. The unanchored and
    no-storage branches remain explicitly outside this function rather than being
    guessed.
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
        if p_index is None:
            continue

        if len(trips) >= max_trips:
            break
        start_interval = trips[p_index].virtual_departure
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
