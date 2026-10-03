from fastapi.routing import APIRoute

from oferbus_api.main import app
from oferbus_api.recalculation import PlanRevisionComparisonResponse, ResultFreshnessResponse


def test_phase_c5_routes_are_exposed() -> None:
    paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    assert "/plans/{plan_revision_id}/result-status" in paths
    assert "/plans/{plan_revision_id}/compare-parent" in paths


def test_needs_recalculation_is_explicit_and_parent_result_is_stale() -> None:
    response = ResultFreshnessResponse(
        plan_revision_id="00000000-0000-0000-0000-000000000002",
        parent_plan_revision_id="00000000-0000-0000-0000-000000000001",
        source_kind="manual",
        status="needs-recalculation",
        inherited_parent_result_status="stale",
        result_snapshot_id=None,
        reason="manual child has no exact result snapshot",
    )
    assert response.status == "needs-recalculation"
    assert response.inherited_parent_result_status == "stale"
    assert response.result_snapshot_id is None


def test_parent_child_comparison_contract_reports_structural_changes() -> None:
    response = PlanRevisionComparisonResponse(
        parent_plan_revision_id="00000000-0000-0000-0000-000000000001",
        child_plan_revision_id="00000000-0000-0000-0000-000000000002",
        parent_revision_no=1,
        child_revision_no=2,
        semantic_layer="legacy-exact",
        changed_trip_count=1,
        changed_block_count=0,
        trip_changes=[{"sequence_no": 7, "changed_fields": ["is_express"]}],
        block_changes=[],
        child_result_status="needs-recalculation",
    )
    assert response.trip_changes[0].changed_fields == ["is_express"]
    assert response.child_result_status == "needs-recalculation"
