import pytest
from oferbus_legacy_core import *


def _op(direction, dep, arr, *, trip_type=0):
    return OperationalTrip(direction, dep, dep, arr, arr, trip_type=trip_type)


def test_trip_type_bitfield_semantics_are_explicit():
    t = _op(1, 60, 80, trip_type=int(TripTypeFlag.EXPRESS | TripTypeFlag.CREATED | TripTypeFlag.USER_OR_IMPORTED | TripTypeFlag.DEPARTURE_CHANGED))
    assert t.is_express
    assert t.was_created
    assert t.was_created_by_user
    assert not t.was_imported
    assert t.departure_was_changed
    imported = _op(1, 60, 80, trip_type=int(TripTypeFlag.USER_OR_IMPORTED))
    assert imported.was_imported
    assert not imported.was_created_by_user


def test_service_level_labels_and_storage_collapse_overload_beyond_f():
    vehicle = VehicleModel(seats=40, free_area_m2=10.0)
    assert service_level_label_legacy(40, vehicle) == "A"
    assert service_level_label_legacy(41, vehicle) == "B"
    assert service_level_label_legacy(115, vehicle) == "F"
    assert service_level_label_legacy(130, vehicle) == "F1"
    assert stored_service_level_legacy(130, vehicle) == 5


def test_passengers_in_period_uses_legacy_strict_half_rounding():
    curve = [0.0, 1.25, 1.25, 0.0]
    assert passengers_in_period_legacy(curve, line_start=60, start_real=60, end_real=61) == 2
    curve2 = [0.0, 1.2501, 1.2501, 0.0]
    assert passengers_in_period_legacy(curve2, line_start=60, start_real=60, end_real=61) == 3


def test_assign_service_level_marks_express_as_minus_one():
    trip = OperationalTrip(1, 60, 60, 70, 70, trip_type=int(TripTypeFlag.EXPRESS), vehicle=1)
    assign_service_levels_legacy(
        [trip],
        demand_curves={1: [0.0, 1.0, 0.0]},
        ir_curves={1: [0.0, 1.0, 0.0]},
        direction_starts={1: 60},
        vehicle_models={1: VehicleModel(40, 10.0)},
    )
    assert trip.service_level == -1
