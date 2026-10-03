from __future__ import annotations

from typing import Mapping

from .operations import LinkKind, OperationalTrip
from .return_trips import _vdep
from .timetable import DirectionPlanningData, MinimumTimetableConfig, PlannedTrip
from .trip_attributes import ExpressTravelParameters, complete_trip_attributes_legacy


def _shift_trip_one_virtual_minute(
    trip: OperationalTrip,
    *,
    directions: Mapping[int, DirectionPlanningData],
    config: MinimumTimetableConfig,
    express_parameters: Mapping[int, ExpressTravelParameters],
) -> OperationalTrip:
    """Port of ``Desloca_Viagem(..., 1)`` used by the fine-adjustment pass."""
    d = directions[trip.direction]
    if trip.is_express:
        departure = trip.real_departure + 1
    else:
        target_virtual = trip.virtual_departure + 1
        departure = trip.real_departure
        while _vdep(d, departure, config) < target_virtual:
            departure += 1
    return complete_trip_attributes_legacy(
        [PlannedTrip(trip.direction, departure, 0, trip.trip_type)],
        directions=directions,
        config=config,
        line_number=trip.line,
        express_parameters=express_parameters,
    )[0]


def fine_adjustment_one_minute_legacy(
    trips: list[OperationalTrip],
    *,
    directions: Mapping[int, DirectionPlanningData],
    config: MinimumTimetableConfig,
    express_parameters: Mapping[int, ExpressTravelParameters] | None = None,
    preserve_bc007_link_variable_bug: bool = True,
) -> int:
    """Reconstruct ``Verifica_Ajuste_1`` and its one-minute displacement.

    The pass looks for a trip departing exactly when another trip arrives and shifts
    the departure by one virtual minute when neither side is already protected by
    a direct-trip link.

    BC-007 (Bug Candidate 007): 2008c assigns both ``valorI`` and ``valorJ`` from
    trip ``i``. With ``preserve_bc007_link_variable_bug=False``, ``valorJ`` is read
    from candidate trip ``j``, which is the strongly suggested intended guard.
    """
    if not trips:
        return 0
    express_parameters = express_parameters or {}
    moved = 0
    n = len(trips)
    i = 0
    while i < n:
        current = trips[i]
        j = i
        while j < n - 1 and trips[j].virtual_departure <= current.virtual_arrival:
            candidate = trips[j]
            opposite = 3 - current.direction if config.radial else 1
            found = (
                current.virtual_arrival == candidate.virtual_departure
                and candidate.direction == opposite
            )
            value_i = current.legacy_links
            value_j = current.legacy_links if preserve_bc007_link_variable_bug else candidate.legacy_links
            found = found and ((value_i // 4) != int(LinkKind.TRIP)) and ((value_j % 4) != int(LinkKind.TRIP))
            if found:
                trips[j] = _shift_trip_one_virtual_minute(
                    candidate,
                    directions=directions,
                    config=config,
                    express_parameters=express_parameters,
                )
                moved += 1
            j += 1
        i += 1
    if moved:
        trips.sort(key=lambda t: t.virtual_departure)
    return moved
