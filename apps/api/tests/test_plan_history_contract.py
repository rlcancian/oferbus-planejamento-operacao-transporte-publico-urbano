from oferbus_api.history import RevisionHistoryResponse, router as history_router
from oferbus_api.main import app


def test_c6_history_route_is_tenant_guarded_and_exposed() -> None:
    router_paths = {route.path for route in history_router.routes}
    assert "/plans/{plan_revision_id}/history" in router_paths
    assert "/plans/{plan_revision_id}/history" in app.openapi()["paths"]


def test_c6_history_contract_has_explicit_undo_and_redo_surfaces() -> None:
    fields = RevisionHistoryResponse.model_fields
    assert "ancestors" in fields
    assert "redo_candidates" in fields
    assert "current_plan_revision_id" in fields
