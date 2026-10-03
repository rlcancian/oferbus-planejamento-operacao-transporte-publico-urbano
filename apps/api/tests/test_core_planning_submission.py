import uuid

import pytest
from fastapi import HTTPException

from oferbus_core import (
    CostPlanningInput,
    DirectionPlanningInput,
    ObservedTripInput,
    PlanningInput,
    PlanningSpecification,
    SemanticLayer,
    VehiclePlanningInput,
    fingerprint,
)
from oferbus_api import computations
from oferbus_api.identity import Principal, Role


def _planning_input() -> PlanningInput:
    start, end = 60, 120
    service_minutes = end - start + 1
    return PlanningInput(
        semantic_layer=SemanticLayer.NORMALIZED,
        directions=(
            DirectionPlanningInput(
                direction_key="outbound",
                legacy_direction_number=1,
                observations=(
                    ObservedTripInput(60, 10, critical_passengers=10, travel_time_min=10),
                    ObservedTripInput(90, 10, critical_passengers=10, travel_time_min=10),
                    ObservedTripInput(120, 10, critical_passengers=10, travel_time_min=10),
                ),
                demand_passengers_per_minute=tuple([0.0] + [1.0] * service_minutes + [0.0]),
                renewal_index_curve=tuple([0.0] + [1.0] * service_minutes + [0.0]),
                travel_time_min_curve=tuple([0.0] + [10.0] * service_minutes + [0.0]),
                service_start_minute=start,
                service_end_minute=end,
                demand_maximum_passengers_per_minute=1.0,
                extension_km=8.0,
                storage_at_departure_terminal=True,
            ),
        ),
        vehicle=VehiclePlanningInput(seats=20, free_area_m2=10.0, capacity_level=1),
        cost=CostPlanningInput(mode="per_km", cost_per_km=2.0),
        specification=PlanningSpecification(
            max_headway_min=20,
            project_capacity_passengers=10.0,
            valley_capacity_passengers=10.0,
            boarding_seconds_per_passenger=0.0,
            alighting_seconds_per_passenger=0.0,
            radial=False,
        ),
    )


def _principal() -> Principal:
    return Principal(
        user_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        subject="test:planner",
        display_name="Test Planner",
        role=Role.PLANNER,
    )


def test_core_planning_submission_derives_authoritative_snapshot_metadata(monkeypatch) -> None:
    planning_input = _planning_input()
    principal = _principal()
    scenario_revision_id = uuid.uuid4()
    monkeypatch.setattr(computations, "load_planning_input", lambda organization_id, revision_id: planning_input)

    submission = computations._submission(
        computations.ComputationSubmitRequest(
            scenario_revision_id=scenario_revision_id,
            run_kind="core-planning",
            idempotency_key="core-planning-test",
        ),
        principal,
    )

    assert submission.organization_id == principal.organization_id
    assert submission.scenario_revision_id == scenario_revision_id
    assert submission.run_kind == "core-planning"
    assert submission.semantic_layer == "normalized"
    assert submission.engine_version == computations.CORE_ENGINE_DESCRIPTOR
    assert submission.input_fingerprint == fingerprint(planning_input)
    assert submission.payload == {}


def test_core_planning_rejects_ad_hoc_payload_before_loading_snapshot(monkeypatch) -> None:
    principal = _principal()
    loaded = False

    def load(*args, **kwargs):
        nonlocal loaded
        loaded = True
        return _planning_input()

    monkeypatch.setattr(computations, "load_planning_input", load)

    with pytest.raises(HTTPException) as exc_info:
        computations._submission(
            computations.ComputationSubmitRequest(
                scenario_revision_id=uuid.uuid4(),
                run_kind="core-planning",
                payload={"max_headway_min": 5},
            ),
            principal,
        )

    assert exc_info.value.status_code == 422
    assert loaded is False


def test_core_planning_rejects_requested_semantic_layer_mismatch(monkeypatch) -> None:
    planning_input = _planning_input()
    monkeypatch.setattr(computations, "load_planning_input", lambda organization_id, revision_id: planning_input)

    with pytest.raises(HTTPException) as exc_info:
        computations._submission(
            computations.ComputationSubmitRequest(
                scenario_revision_id=uuid.uuid4(),
                run_kind="core-planning",
                semantic_layer="legacy-exact",
            ),
            _principal(),
        )

    assert exc_info.value.status_code == 422
    assert "does not match" in str(exc_info.value.detail)
