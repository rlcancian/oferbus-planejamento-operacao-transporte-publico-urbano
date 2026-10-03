import uuid

import pytest
from pydantic import TypeAdapter, ValidationError

from oferbus_api.edits import ForkPlanRequest, MoveTripRequest, PlanEditRequest, SetTripExpressRequest
from oferbus_api.main import app


def test_c4_edit_boundary_exposes_only_characterized_typed_commands() -> None:
    fork = ForkPlanRequest(client_command_id=uuid.uuid4(), command_type="fork", reason="Create an immutable manual working revision.")
    move = MoveTripRequest(client_command_id=uuid.uuid4(), command_type="move-trip", reason="Move one trip while preserving its duration.", trip_sequence_no=2, departure_service_minute=91)
    express = SetTripExpressRequest(client_command_id=uuid.uuid4(), command_type="set-trip-express", reason="Mark the operational trip as express.", trip_sequence_no=2, is_express=True)
    assert fork.command_type == "fork"; assert move.command_type == "move-trip"; assert express.command_type == "set-trip-express"; assert express.is_express is True
    adapter = TypeAdapter(PlanEditRequest)
    for unsupported in ("arbitrary-json-patch", "create-trip", "remove-trip", "set-trip-type", "assign-trip-block"):
        with pytest.raises(ValidationError):
            adapter.validate_python({"client_command_id": str(uuid.uuid4()), "command_type": unsupported, "reason": "Uncharacterized C.4 mutation must fail closed."})


def test_c3_temporal_command_requires_integer_service_minutes() -> None:
    with pytest.raises(ValidationError):
        MoveTripRequest(client_command_id=uuid.uuid4(), command_type="move-trip", reason="Fractional service minutes are outside the domain contract.", trip_sequence_no=1, departure_service_minute=60.5)


def test_c4_edit_endpoint_is_in_openapi() -> None:
    schema = app.openapi(); operation = schema["paths"]["/plans/{plan_revision_id}/edits"]["post"]; assert operation
