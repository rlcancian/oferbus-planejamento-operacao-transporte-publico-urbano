import pytest

from oferbus_legacy_core import *


def _direction(*, start=40, end=160, tt=10.0, storage=True):
    total = end - start + 1
    return DirectionPlanningData(
        observed=(TripObservation(start, 1), TripObservation(end, 1)),
        demand_curve=tuple([0.0] + [1.0] * total + [0.0]),
        ir_curve=tuple([0.0] + [1.0] * total + [0.0]),
        travel_time_curve=tuple([0.0] + [tt] * total + [0.0]),
        start=start,
        end=end,
        maximum=1.0,
        storage_at_departure_terminal=storage,
    )


def _config(*, radial=True):
    return MinimumTimetableConfig(
        max_interval=20,
        project_capacity=10.0,
        valley_capacity=10.0,
        boarding_seconds=0.0,
        alighting_seconds=0.0,
        radial=radial,
        create_express_returns=False,
    )


def _trip(direction, dep, arr, *, entry=LinkKind.NONE, exit=LinkKind.NONE):
    return OperationalTrip(
        direction=direction,
        real_departure=dep,
        virtual_departure=dep,
        real_arrival=arr,
        virtual_arrival=arr,
        entry_link=entry,
        exit_link=exit,
    )


def test_cria2_storage_branch_inserts_return_and_rewrites_links():
    trips = [
        _trip(2, 50, 60),
        _trip(1, 60, 80),
        _trip(2, 70, 80),
        _trip(2, 100, 110),
        _trip(1, 120, 130),
    ]
    created = create_return_trips_cria_2_storage_branch_legacy(
        trips,
        directions={1: _direction(storage=True), 2: _direction(storage=True)},
        config=_config(),
    )
    assert created == 1
    inserted = [t for t in trips if t.direction == 2 and t.trip_type == int(TripTypeFlag.CREATED)][0]
    assert inserted.real_departure == 85
    assert inserted.real_arrival == 95
    assert inserted.entry_link == LinkKind.TRIP
    assert inserted.exit_link == LinkKind.STORAGE
    current = [t for t in trips if t.direction == 1 and t.real_departure == 60][0]
    target = [t for t in trips if t.direction == 1 and t.real_departure == 120][0]
    assert current.exit_link == LinkKind.TRIP
    assert target.entry_link == LinkKind.STORAGE


def test_bc007_link_variable_typo_blocks_a_valid_fine_adjustment():
    current = _trip(1, 60, 80, entry=LinkKind.TRIP, exit=LinkKind.STORAGE)
    candidate = _trip(2, 80, 90, entry=LinkKind.NONE, exit=LinkKind.STORAGE)
    tail = _trip(1, 130, 140)
    directions = {1: _direction(), 2: _direction()}

    legacy = [current, candidate, tail]
    moved_legacy = fine_adjustment_one_minute_legacy(
        legacy,
        directions=directions,
        config=_config(),
        preserve_bc007_link_variable_bug=True,
    )
    assert moved_legacy == 0
    assert [t for t in legacy if t.direction == 2][0].real_departure == 80

    current2 = _trip(1, 60, 80, entry=LinkKind.TRIP, exit=LinkKind.STORAGE)
    candidate2 = _trip(2, 80, 90, entry=LinkKind.NONE, exit=LinkKind.STORAGE)
    tail2 = _trip(1, 130, 140)
    corrected = [current2, candidate2, tail2]
    moved_corrected = fine_adjustment_one_minute_legacy(
        corrected,
        directions=directions,
        config=_config(),
        preserve_bc007_link_variable_bug=False,
    )
    assert moved_corrected == 1
    shifted = [t for t in corrected if t.direction == 2][0]
    assert shifted.real_departure == 81
    assert shifted.entry_link == LinkKind.NONE
    assert shifted.exit_link == LinkKind.NONE
    assert shifted.vehicle == 0
