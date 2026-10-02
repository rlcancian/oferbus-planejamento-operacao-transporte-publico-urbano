from oferbus_legacy_core import *


def _direction(start=60, end=140, tt=10.0):
    total = end - start + 1
    return DirectionPlanningData(
        observed=(TripObservation(start, 1), TripObservation(end, 1)),
        demand_curve=tuple([0.0] + [1.0] * total + [0.0]),
        ir_curve=tuple([0.0] + [1.0] * total + [0.0]),
        travel_time_curve=tuple([0.0] + [tt] * total + [0.0]),
        start=start,
        end=end,
        maximum=1.0,
        storage_at_departure_terminal=True,
    )


def _config():
    return MinimumTimetableConfig(
        max_interval=20,
        project_capacity=10.0,
        valley_capacity=10.0,
        boarding_seconds=0.0,
        alighting_seconds=0.0,
        radial=True,
        create_express_returns=False,
    )


def _trip(direction, dep, arr, *, entry=LinkKind.NONE, exit=LinkKind.NONE):
    return OperationalTrip(direction, dep, dep, arr, arr, entry_link=entry, exit_link=exit)


def test_cria1_inserts_nonexpress_return_between_unresolved_same_direction_trips():
    trips = [
        _trip(1, 60, 80),
        _trip(2, 100, 110, entry=LinkKind.TRIP),
        _trip(1, 110, 120),
        _trip(2, 130, 140),
    ]
    created = create_return_trips_cria_1_legacy(
        trips,
        directions={1: _direction(), 2: _direction()},
        config=_config(),
        preserve_normal_return_type_bug=True,
    )
    assert created == 1
    inserted = [t for t in trips if t.direction == 2 and t.real_departure == 90][0]
    assert inserted.real_arrival == 100
    assert inserted.entry_link == inserted.exit_link == LinkKind.TRIP
    assert inserted.trip_type == 0
    assert trips[0].exit_link == LinkKind.TRIP
    target = [t for t in trips if t.direction == 1 and t.real_departure == 110][0]
    assert target.entry_link == LinkKind.TRIP


def test_cria1_can_expose_intended_created_bit_without_silent_legacy_change():
    trips = [
        _trip(1, 60, 80),
        _trip(2, 100, 110, entry=LinkKind.TRIP),
        _trip(1, 110, 120),
        _trip(2, 130, 140),
    ]
    create_return_trips_cria_1_legacy(
        trips,
        directions={1: _direction(), 2: _direction()},
        config=_config(),
        preserve_normal_return_type_bug=False,
    )
    inserted = [t for t in trips if t.direction == 2 and t.real_departure == 90][0]
    assert inserted.trip_type == int(TripTypeFlag.CREATED)
