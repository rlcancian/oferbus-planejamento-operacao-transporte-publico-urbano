from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from typing import Sequence


class LinkKind(IntEnum):
    NONE = 0
    GARAGE = 1
    STORAGE = 2
    TRIP = 3


@dataclass
class OperationalTrip:
    """Modern explicit representation of the recovered ``TpObjViagem`` semantics.

    ``legacy_links`` is intentionally not stored as the source of truth. Entry and
    exit links are first-class typed fields; encode/decode helpers exist only for
    archaeological parity and migration.
    """

    direction: int
    real_departure: int
    virtual_departure: int
    real_arrival: int
    virtual_arrival: int
    trip_type: int = 0
    line: int = 0
    entry_link: LinkKind = LinkKind.NONE
    exit_link: LinkKind = LinkKind.NONE
    vehicle: int = 0
    driver_code: int = 0
    conductor_code: int = 0
    service_level: int | None = None

    @property
    def is_express(self) -> bool:
        return (self.trip_type % 2) == 1

    @property
    def manual_entry_link(self) -> bool:
        return (self.trip_type & 16) != 0

    @property
    def manual_exit_link(self) -> bool:
        return (self.trip_type & 32) != 0

    @property
    def legacy_links(self) -> int:
        return encode_legacy_links(self.entry_link, self.exit_link)


def encode_legacy_links(entry: LinkKind | int, exit: LinkKind | int) -> int:
    """Exact ``Seta_Vinculo`` packing: A=mod 4, B=integer division by 4."""
    a = int(entry)
    b = int(exit)
    if not 0 <= a <= 3 or not 0 <= b <= 3:
        raise ValueError("legacy link code must be in [0, 3]")
    return b * 4 + a


def decode_legacy_links(value: int) -> tuple[LinkKind, LinkKind]:
    if value < 0:
        raise ValueError("legacy link value must be non-negative")
    return LinkKind(value % 4), LinkKind(value // 4)


def clear_non_manual_links(trips: Sequence[OperationalTrip]) -> None:
    """Port of ``Anula_Vinculos`` without hiding manual overrides.

    Type bit 16 protects the entry link; bit 32 protects the exit link. Vehicle
    assignments are always cleared before rebuilding the chains.
    """
    for trip in trips:
        if not trip.manual_entry_link:
            trip.entry_link = LinkKind.NONE
        if not trip.manual_exit_link:
            trip.exit_link = LinkKind.NONE
        trip.vehicle = 0


def _opposite_direction(direction: int, radial: bool) -> int:
    return 3 - direction if radial else 1


def link_direct_trips_legacy(trips: Sequence[OperationalTrip], *, radial: bool) -> int:
    """Port of ``MMARCHA1.Vincula_Viagens``.

    The collection is expected in ascending virtual-time order. For each trip with
    no exit link, the procedure considers the first future opposite-direction trip
    with no entry link. It only links the pair when no later arrival in the same
    direction can claim that departure more appropriately.

    Returns the number of direct links created; the VB procedure accepted a vehicle
    counter but did not use it in the recovered 2008c body.
    """
    created = 0
    n = len(trips)
    for i in range(n):
        current = trips[i]
        if current.exit_link != LinkKind.NONE:
            continue
        opposite = _opposite_direction(current.direction, radial)

        j: int | None = None
        for candidate_idx in range(n):
            candidate = trips[candidate_idx]
            if (
                candidate.virtual_departure > current.virtual_arrival
                and candidate.direction == opposite
                and candidate.entry_link == LinkKind.NONE
            ):
                j = candidate_idx
                break
        if j is None:
            continue

        later_arrival_exists = any(
            candidate.virtual_arrival > current.virtual_arrival
            and candidate.virtual_arrival < trips[j].virtual_departure
            and candidate.direction == current.direction
            for candidate in trips
        )
        if not later_arrival_exists:
            current.exit_link = LinkKind.TRIP
            trips[j].entry_link = LinkKind.TRIP
            created += 1
    return created


def link_storage_legacy(trips: Sequence[OperationalTrip], *, radial: bool) -> int:
    """Port of the active body of ``Vincula_Estocagens``.

    The 2008c body no longer checks the AreaEstocagem flag at this stage (the old
    conditional is commented out). It links unresolved arrivals to the first future
    compatible departure through STORAGE.
    """
    created = 0
    n = len(trips)
    for i in range(n):
        current = trips[i]
        if current.exit_link != LinkKind.NONE:
            continue
        opposite = _opposite_direction(current.direction, radial)
        for j in range(n):
            candidate = trips[j]
            if (
                candidate.virtual_departure > current.virtual_arrival
                and candidate.direction == opposite
                and candidate.entry_link == LinkKind.NONE
            ):
                current.exit_link = LinkKind.STORAGE
                candidate.entry_link = LinkKind.STORAGE
                created += 1
                break
    return created


def link_garages_legacy(trips: Sequence[OperationalTrip]) -> None:
    """Port of ``Vincula_Garagens``: all unresolved ends become GARAGE."""
    for trip in trips:
        if trip.entry_link == LinkKind.NONE:
            trip.entry_link = LinkKind.GARAGE
        if trip.exit_link == LinkKind.NONE:
            trip.exit_link = LinkKind.GARAGE


def allocate_fleet_legacy(trips: Sequence[OperationalTrip], *, radial: bool) -> int:
    """Port of ``MPROCEDI.Ajusta_Alocacao_Da_Frota``.

    A vehicle number is created at each unassigned chain head and propagated to
    future compatible trips. Compatibility requires temporal feasibility, direction
    transition, and exact equality between predecessor exit-link code and successor
    entry-link code. Returns the effective fleet size.
    """
    vehicle_count = 0
    n = len(trips)
    for i in range(n):
        if trips[i].vehicle != 0:
            continue
        vehicle_count += 1
        trips[i].vehicle = vehicle_count
        if trips[i].exit_link == LinkKind.GARAGE:
            continue

        direction = trips[i].direction
        opposite = _opposite_direction(direction, radial)
        j = i
        for k in range(i + 1, n):
            candidate = trips[k]
            can_chain = (
                candidate.virtual_departure > trips[j].virtual_arrival
                and candidate.direction == opposite
                and candidate.vehicle == 0
                and candidate.entry_link == trips[j].exit_link
            )
            if can_chain:
                candidate.vehicle = vehicle_count
                j = k
                direction = opposite
                opposite = _opposite_direction(direction, radial)
    return vehicle_count


def build_basic_link_graph_legacy(trips: Sequence[OperationalTrip], *, radial: bool) -> int:
    """Characterization subset of ``Constroi_Grafico_De_Marcha``.

    This deliberately excludes ``Cria_1``, ``Cria_2``, ``Verifica_Ida_Garagem`` and
    fine adjustment. It is the source-confirmed stable chain:

    direct trip links -> storage links -> garage completion -> fleet allocation.
    """
    link_direct_trips_legacy(trips, radial=radial)
    link_storage_legacy(trips, radial=radial)
    link_garages_legacy(trips)
    return allocate_fleet_legacy(trips, radial=radial)


def vehicle_blocks(trips: Sequence[OperationalTrip]) -> dict[int, list[OperationalTrip]]:
    blocks: dict[int, list[OperationalTrip]] = {}
    for trip in trips:
        if trip.vehicle <= 0:
            continue
        blocks.setdefault(trip.vehicle, []).append(trip)
    return blocks
