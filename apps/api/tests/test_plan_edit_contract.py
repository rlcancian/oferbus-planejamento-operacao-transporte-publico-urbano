import uuid

import pytest
from pydantic import ValidationError

from oferbus_api.edits import ForkPlanRequest, MoveTripRequest, SetTripExpressRequest
from oferbus_api.main import app


def test_c2_edit_boundary_keeps_typed_fork_command() -> None:
    request = ForkPlanRequest(
        client_command_id=uuid.uuid4(),
        command_type="fork",
        reason="Create an immutable manual working revision.",
    )
    assert request.command_type == "fork"

    with pytest.raises(ValidationError):
        ForkPlanRequest(
            client_command_id=uuid.uuid4(),
            command_type="arbitrary-json-patch",
            reason="This must not bypass the typed command boundary.",
        )


def test_c3_move_trip_contract_uses_integer_service_minutes() -> None:
    request = MoveTripRequest(
        client_command_id=uuid.uuid4(),
        command_type="move-trip",
        reason="Move one trip without mutating its parent revision.",
        trip_sequence_no=1,
        departure_service_minute=59,
    )
    assert request.trip_sequence_no == 1
    assert request.departure_service_minute == 59

    with pytest.raises(ValidationError):
        MoveTripRequest(
            client_command_id=uuid.uuid4(),
            command_type="move-trip",
            reason="Negative service minutes are invalid.",
            trip_sequence_no=1,
            departure_service_minute=-1,
        )


def test_c4_express_edit_is_typed_and_boolean() -> None:
    request = SetTripExpressRequest(
        client_command_id=uuid.uuid4(),
        command_type="set-trip-express",
        reason="Mark the characterized trip as express in a child revision.",
        trip_sequence_no=1,
        is_express=True,
    )
    assert request.command_type == "set-trip-express"
    assert request.trip_sequence_no == 1
    assert request.is_express is True

    with pytest.raises(ValidationError):
        SetTripExpressRequest(
            client_command_id=uuid.uuid4(),
            command_type="assign-trip-block",
            reason="Uncharacterized block mutation must not cross the typed boundary.",
            trip_sequence_no=1,
            is_express=True,
        )


def test_edit_endpoint_is_in_openapi() -> None:
    schema = app.openapi()
    assert "/plans/{plan_revision_id}/edits" in schema["paths"]
    assert "post" in schema["paths"]["/plans/{plan_revision_id}/edits"]
