from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func, select

from oferbus_core import (
    CostPlanningInput,
    DirectionPlanningInput,
    ObservedTripInput,
    PlanningInput,
    PlanningSpecification,
    SemanticLayer,
    VehiclePlanningInput,
    fingerprint,
    validate_planning_input,
)
from oferbus_db import (
    LineDirection,
    ObservedTripDataset,
    ObservedTripDatasetRevision,
    ObservedTripObservation,
    Scenario,
    ScenarioDirectionPlanningInput,
    ScenarioPlanningInput,
    ScenarioRevision,
    TransitLine,
    get_session_factory,
)


class PlanningInputError(ValueError):
    pass


class PlanningInputNotFound(PlanningInputError):
    pass


class PlanningInputIntegrityError(PlanningInputError):
    pass


@dataclass(frozen=True)
class DirectionObservationBatch:
    direction_id: uuid.UUID
    observations: tuple[ObservedTripInput, ...]


@dataclass(frozen=True)
class CreateObservedDatasetCommand:
    organization_id: uuid.UUID
    created_by: uuid.UUID | None
    line_id: uuid.UUID
    name: str
    description: str | None
    source_label: str | None
    source_metadata: dict | None
    directions: tuple[DirectionObservationBatch, ...]


@dataclass(frozen=True)
class DirectionPlanningSnapshotCommand:
    direction_id: uuid.UUID
    dataset_revision_id: uuid.UUID
    service_start_minute: int
    service_end_minute: int
    demand_passengers_per_minute: tuple[float, ...]
    renewal_index_curve: tuple[float, ...]
    travel_time_min_curve: tuple[float, ...]
    demand_maximum_passengers_per_minute: float
    storage_at_departure_terminal: bool


@dataclass(frozen=True)
class CreateScenarioRevisionCommand:
    organization_id: uuid.UUID
    created_by: uuid.UUID | None
    scenario_id: uuid.UUID
    parent_revision_id: uuid.UUID | None
    reason: str | None
    semantic_layer: SemanticLayer
    vehicle: VehiclePlanningInput
    cost: CostPlanningInput
    specification: PlanningSpecification
    directions: tuple[DirectionPlanningSnapshotCommand, ...]


@dataclass(frozen=True)
class DatasetRevisionCreated:
    dataset_id: uuid.UUID
    dataset_revision_id: uuid.UUID
    revision_no: int
    content_fingerprint: str


@dataclass(frozen=True)
class ScenarioRevisionCreated:
    scenario_revision_id: uuid.UUID
    revision_no: int
    input_fingerprint: str
    planning_input: PlanningInput


def _direction_payload(batch: DirectionObservationBatch) -> dict[str, object]:
    return {
        "direction_id": str(batch.direction_id),
        "observations": [
            {
                "departure_service_minute": item.departure_service_minute,
                "passengers": item.passengers,
                "critical_passengers": item.critical_passengers,
                "travel_time_min": item.travel_time_min,
            }
            for item in batch.observations
        ],
    }


def create_observed_dataset(command: CreateObservedDatasetCommand) -> DatasetRevisionCreated:
    if not command.name.strip():
        raise PlanningInputError("dataset name must not be empty")
    if not command.directions:
        raise PlanningInputError("dataset requires at least one direction")
    if len({item.direction_id for item in command.directions}) != len(command.directions):
        raise PlanningInputError("dataset contains duplicate direction ids")
    if any(not item.observations for item in command.directions):
        raise PlanningInputError("every dataset direction requires at least one observation")

    payload = {
        "line_id": str(command.line_id),
        "directions": [_direction_payload(item) for item in sorted(command.directions, key=lambda x: str(x.direction_id))],
    }
    content_fingerprint = fingerprint(payload)
    dataset_id = uuid.uuid4()
    revision_id = uuid.uuid4()

    session_factory = get_session_factory()
    with session_factory() as session:
        line = session.execute(
            select(TransitLine).where(
                TransitLine.organization_id == command.organization_id,
                TransitLine.id == command.line_id,
            )
        ).scalar_one_or_none()
        if line is None:
            raise PlanningInputNotFound("transit line not found in active organization")

        directions: dict[uuid.UUID, LineDirection] = {}
        for batch in command.directions:
            direction = session.execute(
                select(LineDirection).where(
                    LineDirection.organization_id == command.organization_id,
                    LineDirection.id == batch.direction_id,
                    LineDirection.line_id == command.line_id,
                )
            ).scalar_one_or_none()
            if direction is None:
                raise PlanningInputNotFound("line direction not found for dataset line")
            directions[batch.direction_id] = direction

        session.add(
            ObservedTripDataset(
                id=dataset_id,
                organization_id=command.organization_id,
                line_id=command.line_id,
                name=command.name.strip(),
                description=command.description,
                status="active",
                created_by=command.created_by,
            )
        )
        session.add(
            ObservedTripDatasetRevision(
                id=revision_id,
                organization_id=command.organization_id,
                dataset_id=dataset_id,
                revision_no=1,
                parent_revision_id=None,
                source_label=command.source_label,
                source_metadata=command.source_metadata,
                content_fingerprint=content_fingerprint,
                created_by=command.created_by,
            )
        )

        for batch in command.directions:
            for sequence_no, observed in enumerate(batch.observations, start=1):
                session.add(
                    ObservedTripObservation(
                        organization_id=command.organization_id,
                        dataset_revision_id=revision_id,
                        direction_id=batch.direction_id,
                        sequence_no=sequence_no,
                        departure_service_minute=observed.departure_service_minute,
                        passengers=observed.passengers,
                        critical_passengers=observed.critical_passengers,
                        travel_time_min=observed.travel_time_min,
                    )
                )

        session.commit()

    return DatasetRevisionCreated(
        dataset_id=dataset_id,
        dataset_revision_id=revision_id,
        revision_no=1,
        content_fingerprint=content_fingerprint,
    )


def _observations_for_direction(
    session,
    *,
    organization_id: uuid.UUID,
    dataset_revision_id: uuid.UUID,
    direction_id: uuid.UUID,
) -> tuple[ObservedTripInput, ...]:
    rows = session.execute(
        select(ObservedTripObservation)
        .where(
            ObservedTripObservation.organization_id == organization_id,
            ObservedTripObservation.dataset_revision_id == dataset_revision_id,
            ObservedTripObservation.direction_id == direction_id,
        )
        .order_by(ObservedTripObservation.sequence_no)
    ).scalars().all()
    if not rows:
        raise PlanningInputIntegrityError("dataset revision has no observations for selected direction")
    return tuple(
        ObservedTripInput(
            departure_service_minute=item.departure_service_minute,
            passengers=item.passengers,
            critical_passengers=item.critical_passengers,
            travel_time_min=item.travel_time_min,
        )
        for item in rows
    )


def create_scenario_revision(command: CreateScenarioRevisionCommand) -> ScenarioRevisionCreated:
    if not command.directions:
        raise PlanningInputError("scenario revision requires at least one direction")
    if len({item.direction_id for item in command.directions}) != len(command.directions):
        raise PlanningInputError("scenario revision contains duplicate direction ids")

    session_factory = get_session_factory()
    with session_factory() as session:
        scenario = session.execute(
            select(Scenario)
            .where(
                Scenario.organization_id == command.organization_id,
                Scenario.id == command.scenario_id,
            )
            .with_for_update()
        ).scalar_one_or_none()
        if scenario is None:
            raise PlanningInputNotFound("scenario not found in active organization")

        if command.parent_revision_id is not None:
            parent = session.execute(
                select(ScenarioRevision).where(
                    ScenarioRevision.organization_id == command.organization_id,
                    ScenarioRevision.id == command.parent_revision_id,
                    ScenarioRevision.scenario_id == command.scenario_id,
                )
            ).scalar_one_or_none()
            if parent is None:
                raise PlanningInputNotFound("parent scenario revision not found")

        core_directions: list[DirectionPlanningInput] = []
        persistence_rows: list[tuple[DirectionPlanningSnapshotCommand, LineDirection]] = []

        for requested in command.directions:
            direction = session.execute(
                select(LineDirection).where(
                    LineDirection.organization_id == command.organization_id,
                    LineDirection.id == requested.direction_id,
                )
            ).scalar_one_or_none()
            if direction is None:
                raise PlanningInputNotFound("line direction not found in active organization")
            if direction.legacy_direction_number is None:
                raise PlanningInputIntegrityError("selected direction has no legacy direction number")
            if direction.extension_km is None or Decimal(direction.extension_km) <= 0:
                raise PlanningInputIntegrityError("selected direction requires a positive extension_km")

            dataset_revision = session.execute(
                select(ObservedTripDatasetRevision, ObservedTripDataset)
                .join(
                    ObservedTripDataset,
                    ObservedTripDataset.id == ObservedTripDatasetRevision.dataset_id,
                )
                .where(
                    ObservedTripDatasetRevision.organization_id == command.organization_id,
                    ObservedTripDatasetRevision.id == requested.dataset_revision_id,
                    ObservedTripDataset.organization_id == command.organization_id,
                )
            ).first()
            if dataset_revision is None:
                raise PlanningInputNotFound("observed dataset revision not found")
            _, dataset = dataset_revision
            if dataset.line_id != direction.line_id:
                raise PlanningInputIntegrityError("dataset line does not match selected direction line")

            observations = _observations_for_direction(
                session,
                organization_id=command.organization_id,
                dataset_revision_id=requested.dataset_revision_id,
                direction_id=requested.direction_id,
            )
            core_directions.append(
                DirectionPlanningInput(
                    direction_key=direction.direction_key,
                    legacy_direction_number=direction.legacy_direction_number,
                    observations=observations,
                    demand_passengers_per_minute=requested.demand_passengers_per_minute,
                    renewal_index_curve=requested.renewal_index_curve,
                    travel_time_min_curve=requested.travel_time_min_curve,
                    service_start_minute=requested.service_start_minute,
                    service_end_minute=requested.service_end_minute,
                    demand_maximum_passengers_per_minute=requested.demand_maximum_passengers_per_minute,
                    extension_km=float(direction.extension_km),
                    storage_at_departure_terminal=requested.storage_at_departure_terminal,
                )
            )
            persistence_rows.append((requested, direction))

        planning_input = PlanningInput(
            semantic_layer=command.semantic_layer,
            directions=tuple(sorted(core_directions, key=lambda item: item.legacy_direction_number)),
            vehicle=command.vehicle,
            cost=command.cost,
            specification=command.specification,
        )
        validate_planning_input(planning_input)
        input_fingerprint = fingerprint(planning_input)

        current_max = session.execute(
            select(func.max(ScenarioRevision.revision_no)).where(
                ScenarioRevision.organization_id == command.organization_id,
                ScenarioRevision.scenario_id == command.scenario_id,
            )
        ).scalar_one()
        revision_no = int(current_max or 0) + 1
        revision_id = uuid.uuid4()

        session.add(
            ScenarioRevision(
                id=revision_id,
                organization_id=command.organization_id,
                scenario_id=command.scenario_id,
                revision_no=revision_no,
                parent_revision_id=command.parent_revision_id,
                created_by=command.created_by,
                reason=command.reason,
                input_fingerprint=input_fingerprint,
            )
        )
        session.add(
            ScenarioPlanningInput(
                organization_id=command.organization_id,
                scenario_revision_id=revision_id,
                semantic_layer=command.semantic_layer.value,
                vehicle_seats=command.vehicle.seats,
                vehicle_free_area_m2=command.vehicle.free_area_m2,
                vehicle_capacity_level=command.vehicle.capacity_level,
                cost_mode=command.cost.mode,
                cost_per_km=command.cost.cost_per_km,
                fixed_cost_per_vehicle=command.cost.fixed_cost_per_vehicle,
                variable_cost_per_km=command.cost.variable_cost_per_km,
                max_headway_min=command.specification.max_headway_min,
                project_capacity_passengers=command.specification.project_capacity_passengers,
                valley_capacity_passengers=command.specification.valley_capacity_passengers,
                boarding_seconds_per_passenger=command.specification.boarding_seconds_per_passenger,
                alighting_seconds_per_passenger=command.specification.alighting_seconds_per_passenger,
                radial=command.specification.radial,
                create_express_returns=command.specification.create_express_returns,
                mean_renewal_index=command.specification.mean_renewal_index,
                typical_day_participation=command.specification.typical_day_participation,
                equivalent_passenger_index=command.specification.equivalent_passenger_index,
            )
        )

        for requested, direction in persistence_rows:
            session.add(
                ScenarioDirectionPlanningInput(
                    organization_id=command.organization_id,
                    scenario_revision_id=revision_id,
                    direction_id=requested.direction_id,
                    dataset_revision_id=requested.dataset_revision_id,
                    direction_key=direction.direction_key,
                    legacy_direction_number=direction.legacy_direction_number,
                    service_start_minute=requested.service_start_minute,
                    service_end_minute=requested.service_end_minute,
                    demand_passengers_per_minute=list(requested.demand_passengers_per_minute),
                    renewal_index_curve=list(requested.renewal_index_curve),
                    travel_time_min_curve=list(requested.travel_time_min_curve),
                    demand_maximum_passengers_per_minute=requested.demand_maximum_passengers_per_minute,
                    extension_km=direction.extension_km,
                    storage_at_departure_terminal=requested.storage_at_departure_terminal,
                )
            )

        session.commit()

    return ScenarioRevisionCreated(
        scenario_revision_id=revision_id,
        revision_no=revision_no,
        input_fingerprint=input_fingerprint,
        planning_input=planning_input,
    )


def load_planning_input(organization_id: uuid.UUID, scenario_revision_id: uuid.UUID) -> PlanningInput:
    session_factory = get_session_factory()
    with session_factory() as session:
        revision = session.execute(
            select(ScenarioRevision).where(
                ScenarioRevision.organization_id == organization_id,
                ScenarioRevision.id == scenario_revision_id,
            )
        ).scalar_one_or_none()
        if revision is None:
            raise PlanningInputNotFound("scenario revision not found")

        snapshot = session.execute(
            select(ScenarioPlanningInput).where(
                ScenarioPlanningInput.organization_id == organization_id,
                ScenarioPlanningInput.scenario_revision_id == scenario_revision_id,
            )
        ).scalar_one_or_none()
        if snapshot is None:
            raise PlanningInputNotFound("scenario revision has no planning input snapshot")

        direction_rows = session.execute(
            select(ScenarioDirectionPlanningInput)
            .where(
                ScenarioDirectionPlanningInput.organization_id == organization_id,
                ScenarioDirectionPlanningInput.scenario_revision_id == scenario_revision_id,
            )
            .order_by(ScenarioDirectionPlanningInput.legacy_direction_number)
        ).scalars().all()
        if not direction_rows:
            raise PlanningInputIntegrityError("scenario revision has no direction planning inputs")

        directions = tuple(
            DirectionPlanningInput(
                direction_key=row.direction_key,
                legacy_direction_number=row.legacy_direction_number,
                observations=_observations_for_direction(
                    session,
                    organization_id=organization_id,
                    dataset_revision_id=row.dataset_revision_id,
                    direction_id=row.direction_id,
                ),
                demand_passengers_per_minute=tuple(float(value) for value in row.demand_passengers_per_minute),
                renewal_index_curve=tuple(float(value) for value in row.renewal_index_curve),
                travel_time_min_curve=tuple(float(value) for value in row.travel_time_min_curve),
                service_start_minute=row.service_start_minute,
                service_end_minute=row.service_end_minute,
                demand_maximum_passengers_per_minute=float(row.demand_maximum_passengers_per_minute),
                extension_km=float(row.extension_km),
                storage_at_departure_terminal=row.storage_at_departure_terminal,
            )
            for row in direction_rows
        )

        planning_input = PlanningInput(
            semantic_layer=SemanticLayer(snapshot.semantic_layer),
            directions=directions,
            vehicle=VehiclePlanningInput(
                seats=snapshot.vehicle_seats,
                free_area_m2=float(snapshot.vehicle_free_area_m2),
                capacity_level=snapshot.vehicle_capacity_level,
            ),
            cost=CostPlanningInput(
                mode=snapshot.cost_mode,
                cost_per_km=float(snapshot.cost_per_km),
                fixed_cost_per_vehicle=float(snapshot.fixed_cost_per_vehicle),
                variable_cost_per_km=float(snapshot.variable_cost_per_km),
            ),
            specification=PlanningSpecification(
                max_headway_min=snapshot.max_headway_min,
                project_capacity_passengers=float(snapshot.project_capacity_passengers),
                valley_capacity_passengers=float(snapshot.valley_capacity_passengers),
                boarding_seconds_per_passenger=float(snapshot.boarding_seconds_per_passenger),
                alighting_seconds_per_passenger=float(snapshot.alighting_seconds_per_passenger),
                radial=snapshot.radial,
                create_express_returns=snapshot.create_express_returns,
                mean_renewal_index=float(snapshot.mean_renewal_index),
                typical_day_participation=float(snapshot.typical_day_participation),
                equivalent_passenger_index=float(snapshot.equivalent_passenger_index),
            ),
        )
        validate_planning_input(planning_input)
        calculated = fingerprint(planning_input)
        if revision.input_fingerprint != calculated:
            raise PlanningInputIntegrityError(
                "scenario revision fingerprint does not match persisted planning input"
            )
        return planning_input
