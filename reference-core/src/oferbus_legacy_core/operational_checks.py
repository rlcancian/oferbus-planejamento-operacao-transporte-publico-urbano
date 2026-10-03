from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .operations import LinkKind, OperationalTrip


@dataclass(frozen=True)
class GarageCheckResult:
    removed_express_trips: int
    predecessor_links_cleared: int
    skipped_after_delete: int


def remove_orphan_express_returns_legacy(
    trips: list[OperationalTrip], *, preserve_post_delete_skip: bool = True
) -> GarageCheckResult:
    """Port of ``MMARCHA1.Verifica_Ida_Garagem``.

    A trip is removed only when its legacy type is exactly 3 (EXPRESS|CREATED)
    and it has no exit link. Before deletion, the source searches backward for an
    opposite-direction trip whose virtual arrival is strictly earlier than the
    express departure and clears that predecessor's exit link.

    BC-011 (Bug Candidate 011): after deleting element ``i`` the VB routine still
    increments ``i``. Therefore an element shifted into the deleted slot is not
    inspected. ``preserve_post_delete_skip=True`` reproduces that behavior.
    """
    removed = 0
    cleared = 0
    skipped = 0
    i = 0
    while i < len(trips):
        trip = trips[i]
        if trip.trip_type == 3 and trip.exit_link == LinkKind.NONE:
            predecessor: int | None = None
            for p in range(i - 1, -1, -1):
                candidate = trips[p]
                if (
                    candidate.virtual_arrival < trip.virtual_departure
                    and candidate.direction == 3 - trip.direction
                ):
                    predecessor = p
                    break
            if predecessor is None:
                raise ValueError(
                    "legacy Verifica_Ida_Garagem would scan before the first trip"
                )
            trips[predecessor].exit_link = LinkKind.NONE
            cleared += 1
            del trips[i]
            removed += 1
            if preserve_post_delete_skip:
                if i < len(trips):
                    skipped += 1
                i += 1
            # normalized behavior deliberately rechecks the element shifted to i
            continue
        i += 1
    return GarageCheckResult(removed, cleared, skipped)


def count_departure_intervals_under_four_minutes_legacy(
    trips_in_virtual_order: Sequence[OperationalTrip], *, radial: bool
) -> int:
    """Port of ``MMARCHA1.Verifica_Intervalo_4Min``.

    The source assumes the global trip array is already ordered by virtual time,
    but the interval itself is measured from ``SaidaReal`` (real departure).
    Express/deadhead trips are not excluded. The result is the number of
    consecutive same-direction departure intervals strictly below four minutes.
    """
    if not trips_in_virtual_order:
        return 0

    current: dict[int, int] = {1: -1, 2: -1}
    first_direction = trips_in_virtual_order[0].direction
    current[first_direction] = 0

    if radial:
        opposite = 3 - first_direction
        for idx in range(1, len(trips_in_virtual_order)):
            if trips_in_virtual_order[idx].direction == opposite:
                current[opposite] = idx
                break

    count = 0
    for idx in range(1, len(trips_in_virtual_order)):
        direction = trips_in_virtual_order[idx].direction
        previous_idx = current.get(direction, -1)
        # Exact source shape: only compare once this index is later than the
        # current marker for the same direction.
        if idx > previous_idx:
            if previous_idx >= 0:
                interval = (
                    trips_in_virtual_order[idx].real_departure
                    - trips_in_virtual_order[previous_idx].real_departure
                )
                if interval < 4:
                    count += 1
            current[direction] = idx
    return count
