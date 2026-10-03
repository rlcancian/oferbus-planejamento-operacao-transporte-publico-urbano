from sqlalchemy import ForeignKeyConstraint, UniqueConstraint

from oferbus_db import Base


def _has_org_id_unique(table_name: str) -> bool:
    table = Base.metadata.tables[f"oferbus.{table_name}"]
    return any(
        isinstance(constraint, UniqueConstraint)
        and {column.name for column in constraint.columns} == {"organization_id", "id"}
        for constraint in table.constraints
    )


def test_tenant_owned_reference_tables_have_composite_identity() -> None:
    for table_name in [
        "municipality", "transit_operator", "terminal", "transit_line",
        "line_direction", "planning_project", "scenario", "scenario_revision",
        "computation_run",
    ]:
        assert _has_org_id_unique(table_name), table_name


def test_cross_tenant_foreign_keys_include_organization_id() -> None:
    expected = {
        "transit_operator": {"fk_transit_operator_tenant_municipality"},
        "transit_line": {"fk_transit_line_tenant_municipality", "fk_transit_line_tenant_operator"},
        "line_direction": {
            "fk_line_direction_tenant_line",
            "fk_line_direction_tenant_origin_terminal",
            "fk_line_direction_tenant_destination_terminal",
        },
        "scenario": {"fk_scenario_tenant_project"},
        "scenario_revision": {"fk_scenario_revision_tenant_scenario", "fk_scenario_revision_tenant_parent"},
        "computation_run": {"fk_computation_run_tenant_scenario_revision"},
    }
    for table_name, expected_names in expected.items():
        table = Base.metadata.tables[f"oferbus.{table_name}"]
        constraints = {
            constraint.name: {column.name for column in constraint.columns}
            for constraint in table.constraints
            if isinstance(constraint, ForeignKeyConstraint) and constraint.name in expected_names
        }
        assert set(constraints) == expected_names
        assert all("organization_id" in columns for columns in constraints.values())
