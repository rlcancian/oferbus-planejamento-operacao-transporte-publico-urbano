from __future__ import annotations

import argparse
import json
import uuid
from decimal import Decimal

from sqlalchemy import select

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
from oferbus_db import (
    AppUser,
    LineDirection,
    Municipality,
    ObservedTripDataset,
    ObservedTripDatasetRevision,
    ObservedTripObservation,
    Organization,
    OrganizationMembership,
    PlanningProject,
    ProjectLine,
    Scenario,
    ScenarioDirectionPlanningInput,
    ScenarioPlanningInput,
    ScenarioRevision,
    Terminal,
    TransitLine,
    TransitOperator,
    get_session_factory,
)
from oferbus_planning import load_planning_input

NAMESPACE = uuid.UUID("f27940e7-98ad-43d7-90d3-d293ab7d5815")
ORGANIZATION_ID = uuid.uuid5(NAMESPACE, "organization:development")
USER_ID = uuid.uuid5(NAMESPACE, "user:rafael-development")
PROJECT_ID = uuid.uuid5(NAMESPACE, "project:phase-a")
SCENARIO_ID = uuid.uuid5(NAMESPACE, "scenario:phase-a")
SCENARIO_REVISION_ID = uuid.uuid5(NAMESPACE, "scenario-revision:phase-a:1")
SUBJECT = "dev:rafael"

MUNICIPALITY_ID = uuid.uuid5(NAMESPACE, "municipality:phase-b")
OPERATOR_ID = uuid.uuid5(NAMESPACE, "operator:phase-b")
ORIGIN_TERMINAL_ID = uuid.uuid5(NAMESPACE, "terminal:phase-b:origin")
DESTINATION_TERMINAL_ID = uuid.uuid5(NAMESPACE, "terminal:phase-b:destination")
LINE_ID = uuid.uuid5(NAMESPACE, "line:phase-b")
DIRECTION_ID = uuid.uuid5(NAMESPACE, "direction:phase-b:1")
DATASET_ID = uuid.uuid5(NAMESPACE, "dataset:phase-b")
DATASET_REVISION_ID = uuid.uuid5(NAMESPACE, "dataset-revision:phase-b:1")
PLANNING_SCENARIO_ID = uuid.uuid5(NAMESPACE, "scenario:phase-b")
PLANNING_SCENARIO_REVISION_ID = uuid.uuid5(NAMESPACE, "scenario-revision:phase-b:1")


def _planning_fixture() -> PlanningInput:
    start, end = 60, 120
    total = end - start + 1
    observations = (
        ObservedTripInput(60, 10, critical_passengers=10, travel_time_min=10),
        ObservedTripInput(90, 10, critical_passengers=10, travel_time_min=10),
        ObservedTripInput(120, 10, critical_passengers=10, travel_time_min=10),
    )
    direction = DirectionPlanningInput(
        direction_key="outbound",
        legacy_direction_number=1,
        observations=observations,
        demand_passengers_per_minute=tuple([0.0] + [1.0] * total + [0.0]),
        renewal_index_curve=tuple([0.0] + [1.0] * total + [0.0]),
        travel_time_min_curve=tuple([0.0] + [10.0] * total + [0.0]),
        service_start_minute=start,
        service_end_minute=end,
        demand_maximum_passengers_per_minute=1.0,
        extension_km=8.0,
        storage_at_departure_terminal=True,
    )
    return PlanningInput(
        semantic_layer=SemanticLayer.NORMALIZED,
        directions=(direction,),
        vehicle=VehiclePlanningInput(seats=20, free_area_m2=10.0, capacity_level=1),
        cost=CostPlanningInput(mode="per_km", cost_per_km=2.0),
        specification=PlanningSpecification(
            max_headway_min=20,
            project_capacity_passengers=10.0,
            valley_capacity_passengers=10.0,
            boarding_seconds_per_passenger=0.0,
            alighting_seconds_per_passenger=0.0,
            radial=False,
            create_express_returns=False,
            mean_renewal_index=1.0,
            typical_day_participation=1.0,
            equivalent_passenger_index=1.0,
        ),
    )


def seed() -> dict[str, str]:
    planning_input = _planning_fixture()
    planning_fingerprint = fingerprint(planning_input)
    dataset_fingerprint = fingerprint(
        {
            "line_id": str(LINE_ID),
            "direction_id": str(DIRECTION_ID),
            "observations": [
                {
                    "departure_service_minute": item.departure_service_minute,
                    "passengers": item.passengers,
                    "critical_passengers": item.critical_passengers,
                    "travel_time_min": item.travel_time_min,
                }
                for item in planning_input.directions[0].observations
            ],
        }
    )

    session_factory = get_session_factory()
    with session_factory() as session:
        organization = session.get(Organization, ORGANIZATION_ID)
        if organization is None:
            organization = Organization(
                id=ORGANIZATION_ID,
                name="OferBus Development",
                organization_type="development",
                status="active",
            )
            session.add(organization)

        user = session.get(AppUser, USER_ID)
        if user is None:
            user = AppUser(
                id=USER_ID,
                display_name="Rafael Cancian (development)",
                email=None,
                external_subject=SUBJECT,
            )
            session.add(user)
        else:
            user.external_subject = SUBJECT

        membership = session.get(OrganizationMembership, (ORGANIZATION_ID, USER_ID))
        if membership is None:
            membership = OrganizationMembership(
                organization_id=ORGANIZATION_ID,
                user_id=USER_ID,
                role_key="owner",
                status="active",
            )
            session.add(membership)
        else:
            membership.role_key = "owner"
            membership.status = "active"

        project = session.get(PlanningProject, PROJECT_ID)
        if project is None:
            project = PlanningProject(
                id=PROJECT_ID,
                organization_id=ORGANIZATION_ID,
                name="OferBus Development Project",
                description="Deterministic development fixture for platform and planning validation.",
                status="active",
                created_by=USER_ID,
            )
            session.add(project)

        scenario = session.get(Scenario, SCENARIO_ID)
        if scenario is None:
            scenario = Scenario(
                id=SCENARIO_ID,
                organization_id=ORGANIZATION_ID,
                project_id=PROJECT_ID,
                name="Phase A Platform Smoke",
                description="Infrastructure-only scenario retained for platform smoke validation.",
                status="active",
                created_by=USER_ID,
            )
            session.add(scenario)

        revision = session.get(ScenarioRevision, SCENARIO_REVISION_ID)
        if revision is None:
            revision = ScenarioRevision(
                id=SCENARIO_REVISION_ID,
                organization_id=ORGANIZATION_ID,
                scenario_id=SCENARIO_ID,
                revision_no=1,
                parent_revision_id=None,
                created_by=USER_ID,
                reason="Phase A deterministic development seed",
                input_fingerprint="phase-a-development-seed-v1",
            )
            session.add(revision)

        municipality = session.get(Municipality, MUNICIPALITY_ID)
        if municipality is None:
            session.add(
                Municipality(
                    id=MUNICIPALITY_ID,
                    organization_id=ORGANIZATION_ID,
                    name="Município de Desenvolvimento OferBus",
                    state_region="SC",
                    country_code="BR",
                )
            )

        operator = session.get(TransitOperator, OPERATOR_ID)
        if operator is None:
            session.add(
                TransitOperator(
                    id=OPERATOR_ID,
                    organization_id=ORGANIZATION_ID,
                    municipality_id=MUNICIPALITY_ID,
                    name="Operadora de Desenvolvimento OferBus",
                )
            )

        if session.get(Terminal, ORIGIN_TERMINAL_ID) is None:
            session.add(
                Terminal(
                    id=ORIGIN_TERMINAL_ID,
                    organization_id=ORGANIZATION_ID,
                    municipality_id=MUNICIPALITY_ID,
                    name="Terminal Origem",
                    allows_storage=True,
                )
            )
        if session.get(Terminal, DESTINATION_TERMINAL_ID) is None:
            session.add(
                Terminal(
                    id=DESTINATION_TERMINAL_ID,
                    organization_id=ORGANIZATION_ID,
                    municipality_id=MUNICIPALITY_ID,
                    name="Terminal Destino",
                    allows_storage=True,
                )
            )

        line = session.get(TransitLine, LINE_ID)
        if line is None:
            session.add(
                TransitLine(
                    id=LINE_ID,
                    organization_id=ORGANIZATION_ID,
                    municipality_id=MUNICIPALITY_ID,
                    operator_id=OPERATOR_ID,
                    public_code="DEV-001",
                    name="Linha de Desenvolvimento OferBus",
                    status="active",
                )
            )

        direction = session.get(LineDirection, DIRECTION_ID)
        if direction is None:
            session.add(
                LineDirection(
                    id=DIRECTION_ID,
                    organization_id=ORGANIZATION_ID,
                    line_id=LINE_ID,
                    direction_key="outbound",
                    origin_terminal_id=ORIGIN_TERMINAL_ID,
                    destination_terminal_id=DESTINATION_TERMINAL_ID,
                    extension_km=Decimal("8.000"),
                    legacy_direction_number=1,
                )
            )

        if session.get(ProjectLine, (PROJECT_ID, LINE_ID)) is None:
            session.add(
                ProjectLine(
                    organization_id=ORGANIZATION_ID,
                    project_id=PROJECT_ID,
                    line_id=LINE_ID,
                )
            )

        dataset = session.get(ObservedTripDataset, DATASET_ID)
        if dataset is None:
            session.add(
                ObservedTripDataset(
                    id=DATASET_ID,
                    organization_id=ORGANIZATION_ID,
                    line_id=LINE_ID,
                    name="Phase B observed trips",
                    description="Deterministic observations derived from the characterized end-to-end fixture.",
                    status="active",
                    created_by=USER_ID,
                )
            )

        dataset_revision = session.get(ObservedTripDatasetRevision, DATASET_REVISION_ID)
        if dataset_revision is None:
            session.add(
                ObservedTripDatasetRevision(
                    id=DATASET_REVISION_ID,
                    organization_id=ORGANIZATION_ID,
                    dataset_id=DATASET_ID,
                    revision_no=1,
                    parent_revision_id=None,
                    source_label="phase-b-characterization-fixture",
                    source_metadata={"purpose": "development and regression"},
                    content_fingerprint=dataset_fingerprint,
                    created_by=USER_ID,
                )
            )

        existing_observations = session.execute(
            select(ObservedTripObservation).where(
                ObservedTripObservation.organization_id == ORGANIZATION_ID,
                ObservedTripObservation.dataset_revision_id == DATASET_REVISION_ID,
                ObservedTripObservation.direction_id == DIRECTION_ID,
            )
        ).scalars().all()
        if not existing_observations:
            for sequence_no, item in enumerate(planning_input.directions[0].observations, start=1):
                session.add(
                    ObservedTripObservation(
                        organization_id=ORGANIZATION_ID,
                        dataset_revision_id=DATASET_REVISION_ID,
                        direction_id=DIRECTION_ID,
                        sequence_no=sequence_no,
                        departure_service_minute=item.departure_service_minute,
                        passengers=item.passengers,
                        critical_passengers=item.critical_passengers,
                        travel_time_min=item.travel_time_min,
                    )
                )

        planning_scenario = session.get(Scenario, PLANNING_SCENARIO_ID)
        if planning_scenario is None:
            session.add(
                Scenario(
                    id=PLANNING_SCENARIO_ID,
                    organization_id=ORGANIZATION_ID,
                    project_id=PROJECT_ID,
                    name="Phase B Core Planning Fixture",
                    description="Immutable normalized planning input used for Phase B integration.",
                    status="active",
                    created_by=USER_ID,
                )
            )

        planning_revision = session.get(ScenarioRevision, PLANNING_SCENARIO_REVISION_ID)
        if planning_revision is None:
            session.add(
                ScenarioRevision(
                    id=PLANNING_SCENARIO_REVISION_ID,
                    organization_id=ORGANIZATION_ID,
                    scenario_id=PLANNING_SCENARIO_ID,
                    revision_no=1,
                    parent_revision_id=None,
                    created_by=USER_ID,
                    reason="Phase B deterministic planning input seed",
                    input_fingerprint=planning_fingerprint,
                )
            )

        if session.get(ScenarioPlanningInput, PLANNING_SCENARIO_REVISION_ID) is None:
            spec = planning_input.specification
            vehicle = planning_input.vehicle
            cost = planning_input.cost
            session.add(
                ScenarioPlanningInput(
                    organization_id=ORGANIZATION_ID,
                    scenario_revision_id=PLANNING_SCENARIO_REVISION_ID,
                    semantic_layer=planning_input.semantic_layer.value,
                    vehicle_seats=vehicle.seats,
                    vehicle_free_area_m2=vehicle.free_area_m2,
                    vehicle_capacity_level=vehicle.capacity_level,
                    cost_mode=cost.mode,
                    cost_per_km=cost.cost_per_km,
                    fixed_cost_per_vehicle=cost.fixed_cost_per_vehicle,
                    variable_cost_per_km=cost.variable_cost_per_km,
                    max_headway_min=spec.max_headway_min,
                    project_capacity_passengers=spec.project_capacity_passengers,
                    valley_capacity_passengers=spec.valley_capacity_passengers,
                    boarding_seconds_per_passenger=spec.boarding_seconds_per_passenger,
                    alighting_seconds_per_passenger=spec.alighting_seconds_per_passenger,
                    radial=spec.radial,
                    create_express_returns=spec.create_express_returns,
                    mean_renewal_index=spec.mean_renewal_index,
                    typical_day_participation=spec.typical_day_participation,
                    equivalent_passenger_index=spec.equivalent_passenger_index,
                )
            )

        if session.get(ScenarioDirectionPlanningInput, (PLANNING_SCENARIO_REVISION_ID, DIRECTION_ID)) is None:
            fixture_direction = planning_input.directions[0]
            session.add(
                ScenarioDirectionPlanningInput(
                    organization_id=ORGANIZATION_ID,
                    scenario_revision_id=PLANNING_SCENARIO_REVISION_ID,
                    direction_id=DIRECTION_ID,
                    dataset_revision_id=DATASET_REVISION_ID,
                    direction_key=fixture_direction.direction_key,
                    legacy_direction_number=fixture_direction.legacy_direction_number,
                    service_start_minute=fixture_direction.service_start_minute,
                    service_end_minute=fixture_direction.service_end_minute,
                    demand_passengers_per_minute=list(fixture_direction.demand_passengers_per_minute),
                    renewal_index_curve=list(fixture_direction.renewal_index_curve),
                    travel_time_min_curve=list(fixture_direction.travel_time_min_curve),
                    demand_maximum_passengers_per_minute=fixture_direction.demand_maximum_passengers_per_minute,
                    extension_km=fixture_direction.extension_km,
                    storage_at_departure_terminal=fixture_direction.storage_at_departure_terminal,
                )
            )

        session.commit()

        session.execute(
            select(OrganizationMembership).where(
                OrganizationMembership.organization_id == ORGANIZATION_ID,
                OrganizationMembership.user_id == USER_ID,
            )
        ).scalar_one()

    restored = load_planning_input(ORGANIZATION_ID, PLANNING_SCENARIO_REVISION_ID)
    if fingerprint(restored) != planning_fingerprint:
        raise RuntimeError("Phase B planning fixture fingerprint mismatch after persistence round-trip")

    return {
        "organization_id": str(ORGANIZATION_ID),
        "user_id": str(USER_ID),
        "subject": SUBJECT,
        "project_id": str(PROJECT_ID),
        "scenario_id": str(SCENARIO_ID),
        "scenario_revision_id": str(SCENARIO_REVISION_ID),
        "line_id": str(LINE_ID),
        "direction_id": str(DIRECTION_ID),
        "dataset_id": str(DATASET_ID),
        "dataset_revision_id": str(DATASET_REVISION_ID),
        "planning_scenario_id": str(PLANNING_SCENARIO_ID),
        "planning_scenario_revision_id": str(PLANNING_SCENARIO_REVISION_ID),
        "planning_input_fingerprint": planning_fingerprint,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed deterministic OferBus development data")
    parser.add_argument("--json", action="store_true", help="emit a single JSON object")
    args = parser.parse_args()

    result = seed()
    if args.json:
        print(json.dumps(result, sort_keys=True))
        return

    print("OferBus development seed ready:")
    for key, value in result.items():
        print(f"  {key}={value}")


if __name__ == "__main__":
    main()
