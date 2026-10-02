import pytest
from oferbus_legacy_core import *
from oferbus_legacy_core.numeric import vb_bankers_round


def _direction(start=60, end=80, tt=10.0):
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
        radial=False,
    )


def test_vb_integer_assignment_uses_ties_to_even_not_oferbus_explicit_rounding():
    assert vb_bankers_round(4.5) == 4
    assert vb_bankers_round(5.5) == 6


def test_complete_normal_trip_attributes_resets_operational_assignments():
    d = _direction(tt=10.0)
    result = complete_trip_attributes_legacy(
        [PlannedTrip(1, 60, 70, 0)], directions={1: d}, config=_config(), line_number=123
    )
    t = result[0]
    assert (t.real_departure, t.real_arrival) == (60, 70)
    assert (t.virtual_departure, t.virtual_arrival) == (60, 70)
    assert t.line == 123
    assert t.entry_link == LinkKind.NONE and t.exit_link == LinkKind.NONE
    assert t.vehicle == t.driver_code == t.conductor_code == 0


def test_complete_express_trip_uses_recovered_express_duration_formula():
    d = _direction(tt=20.0)
    result = complete_trip_attributes_legacy(
        [PlannedTrip(1, 60, 0, int(TripTypeFlag.EXPRESS | TripTypeFlag.CREATED))],
        directions={1: d},
        config=_config(),
        express_parameters={1: ExpressTravelParameters(base_express_minutes=8.0, residual_percent=50.0)},
    )
    t = result[0]
    assert t.virtual_departure == 60
    assert t.real_arrival == 74
    assert t.virtual_arrival == 74
