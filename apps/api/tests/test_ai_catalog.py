from oferbus_api.ai import build_tool_registry


def test_phase_a5_tool_catalog_is_allow_listed() -> None:
    registry = build_tool_registry()
    specs = registry.specs_for_permissions(
        frozenset({"organization:read", "result:read", "computation:run"})
    )

    assert [spec.name for spec in specs] == [
        "computations.get_status",
        "computations.submit_platform_smoke",
        "platform.describe_capabilities",
    ]
    assert all("sql" not in spec.name.lower() for spec in specs)


def test_computation_submission_requires_confirmation() -> None:
    registry = build_tool_registry()
    spec = registry.get_spec("computations.submit_platform_smoke")

    assert spec.risk.value == "compute"
    assert spec.confirmation.value == "required"
