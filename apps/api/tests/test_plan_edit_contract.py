import uuid

import pytest
from pydantic import ValidationError

from oferbus_api.edits import ForkPlanRequest
from oferbus_api.main import app


def test_c2_edit_boundary_exposes_only_typed_fork_command() -> None:
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


def test_c2_edit_endpoint_is_in_openapi() -> None:
    schema = app.openapi()
    assert "/plans/{plan_revision_id}/edits" in schema["paths"]
    assert "post" in schema["paths"]["/plans/{plan_revision_id}/edits"]
