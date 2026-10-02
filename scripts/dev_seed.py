from __future__ import annotations

import argparse
import json
import uuid

from sqlalchemy import select

from oferbus_db import (
    AppUser,
    Organization,
    OrganizationMembership,
    PlanningProject,
    Scenario,
    ScenarioRevision,
    get_session_factory,
)

NAMESPACE = uuid.UUID("f27940e7-98ad-43d7-90d3-d293ab7d5815")
ORGANIZATION_ID = uuid.uuid5(NAMESPACE, "organization:development")
USER_ID = uuid.uuid5(NAMESPACE, "user:rafael-development")
PROJECT_ID = uuid.uuid5(NAMESPACE, "project:phase-a")
SCENARIO_ID = uuid.uuid5(NAMESPACE, "scenario:phase-a")
SCENARIO_REVISION_ID = uuid.uuid5(NAMESPACE, "scenario-revision:phase-a:1")
SUBJECT = "dev:rafael"


def seed() -> dict[str, str]:
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
                name="Phase A Development Project",
                description="Deterministic development fixture for platform validation.",
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
                description="Infrastructure-only scenario used before planning-domain materialization.",
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

        session.commit()

        # Verify the membership remains resolvable after an idempotent seed.
        session.execute(
            select(OrganizationMembership).where(
                OrganizationMembership.organization_id == ORGANIZATION_ID,
                OrganizationMembership.user_id == USER_ID,
            )
        ).scalar_one()

    return {
        "organization_id": str(ORGANIZATION_ID),
        "user_id": str(USER_ID),
        "subject": SUBJECT,
        "project_id": str(PROJECT_ID),
        "scenario_id": str(SCENARIO_ID),
        "scenario_revision_id": str(SCENARIO_REVISION_ID),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed deterministic OferBus Phase A development data")
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
