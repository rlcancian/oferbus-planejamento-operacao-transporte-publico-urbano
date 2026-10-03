from sqlalchemy import Float

from oferbus_db import PlanRevision, PlannedTrip, ResultSnapshot, VehicleBlock, VehicleBlockTrip


def test_result_tables_keep_tenant_and_lineage_constraints() -> None:
    plan = PlanRevision.__table__
    trip = PlannedTrip.__table__
    block = VehicleBlock.__table__
    block_trip = VehicleBlockTrip.__table__
    snapshot = ResultSnapshot.__table__

    assert {"organization_id", "scenario_revision_id", "computation_run_id"} <= set(plan.c.keys())
    assert {"organization_id", "plan_revision_id", "sequence_no"} <= set(trip.c.keys())
    assert {"organization_id", "plan_revision_id", "block_no"} <= set(block.c.keys())
    assert {"organization_id", "plan_revision_id", "block_no", "planned_trip_id"} <= set(block_trip.c.keys())
    assert {"organization_id", "plan_revision_id", "computation_run_id", "output_fingerprint"} <= set(snapshot.c.keys())

    plan_fk_columns = {tuple(element.parent.name for element in fk.elements) for fk in plan.foreign_key_constraints}
    assert ("organization_id", "scenario_revision_id") in plan_fk_columns
    assert ("organization_id", "computation_run_id") in plan_fk_columns

    snapshot_fk_columns = {tuple(element.parent.name for element in fk.elements) for fk in snapshot.foreign_key_constraints}
    assert ("organization_id", "plan_revision_id") in snapshot_fk_columns
    assert ("organization_id", "computation_run_id") in snapshot_fk_columns


def test_result_float_metrics_do_not_quantize_core_output() -> None:
    snapshot = ResultSnapshot.__table__
    for column_name in (
        "mean_extension_km",
        "total_distance_km",
        "mean_occupancy_rate",
        "daily_total_cost",
        "mean_speed_kmh",
    ):
        assert isinstance(snapshot.c[column_name].type, Float)
