from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select

from oferbus_core import (
    PlannedTripResult,
    PlanningMetricsResult,
    PlanningResult,
    SemanticLayer,
    planning_result_fingerprint,
)
from oferbus_db import (
    ComputationRun,
    PlanRevision,
    PlannedTrip,
    ResultSnapshot,
    ScenarioRevision,
    VehicleBlock,
    VehicleBlockTrip,
    get_session_factory,
)


class PlanningResultPersistenceError(RuntimeError):
    pass


class PlanningResultNotFound(PlanningResultPersistenceError):
    pass


class PlanningResultIntegrityError(PlanningResultPersistenceError):
    pass


@dataclass(frozen=True)
class PersistedPlanningResult:
    plan_revision_id: uuid.UUID
    result_snapshot_id: uuid.UUID
    revision_no: int
    planning_result: PlanningResult


def _validate_result_identity(run: ComputationRun, result: PlanningResult) -> None:
    calculated = planning_result_fingerprint(result)
    if calculated != result.output_fingerprint:
        raise PlanningResultIntegrityError("planning result output fingerprint does not match its material content")
    if run.run_kind != "core-planning":
        raise PlanningResultIntegrityError("only core-planning runs may materialize planning results")
    if run.input_fingerprint != result.input_fingerprint:
        raise PlanningResultIntegrityError("computation run and planning result input fingerprints differ")
    if run.semantic_layer != result.semantic_layer.value:
        raise PlanningResultIntegrityError("computation run and planning result semantic layers differ")
    if run.engine_version != f"{result.engine_id}:{result.engine_version}":
        raise PlanningResultIntegrityError("computation run and planning result engine provenance differ")
    if run.output_fingerprint is not None and run.output_fingerprint != result.output_fingerprint:
        raise PlanningResultIntegrityError("computation run already carries a conflicting output fingerprint")


def _validate_blocks(result: PlanningResult) -> None:
    assigned: set[int] = set()
    if len(result.vehicle_blocks) != result.effective_fleet:
        raise PlanningResultIntegrityError("vehicle block count does not match effective fleet")

    for block_no, indexes in result.vehicle_blocks.items():
        if block_no <= 0:
            raise PlanningResultIntegrityError("vehicle block numbers must be positive")
        for index in indexes:
            if index < 0 or index >= len(result.trips):
                raise PlanningResultIntegrityError("vehicle block references a trip index outside the result")
            if index in assigned:
                raise PlanningResultIntegrityError("planned trip belongs to more than one vehicle block")
            if result.trips[index].vehicle_block != block_no:
                raise PlanningResultIntegrityError("vehicle block mapping disagrees with planned trip assignment")
            assigned.add(index)

    for index, trip in enumerate(result.trips):
        if trip.vehicle_block > 0 and index not in assigned:
            raise PlanningResultIntegrityError("planned trip has a vehicle block but is absent from block ordering")


def persist_planning_result(
    organization_id: uuid.UUID,
    computation_run_id: uuid.UUID,
    result: PlanningResult,
) -> PersistedPlanningResult:
    _validate_blocks(result)
    session_factory = get_session_factory()

    with session_factory() as session:
        run = session.execute(
            select(ComputationRun)
            .where(
                ComputationRun.organization_id == organization_id,
                ComputationRun.id == computation_run_id,
            )
            .with_for_update()
        ).scalar_one_or_none()
        if run is None:
            raise PlanningResultNotFound("computation run not found in active organization")
        _validate_result_identity(run, result)

        existing = session.execute(
            select(PlanRevision).where(
                PlanRevision.organization_id == organization_id,
                PlanRevision.computation_run_id == computation_run_id,
            )
        ).scalar_one_or_none()
        if existing is not None:
            if (
                existing.output_fingerprint != result.output_fingerprint
                or existing.input_fingerprint != result.input_fingerprint
                or existing.semantic_layer != result.semantic_layer.value
                or existing.engine_id != result.engine_id
                or existing.engine_version != result.engine_version
            ):
                raise PlanningResultIntegrityError("existing plan revision conflicts with retried computation result")
            session.rollback()
            return load_planning_result(organization_id, computation_run_id)

        scenario_revision = session.execute(
            select(ScenarioRevision)
            .where(
                ScenarioRevision.organization_id == organization_id,
                ScenarioRevision.id == run.scenario_revision_id,
            )
            .with_for_update()
        ).scalar_one_or_none()
        if scenario_revision is None:
            raise PlanningResultNotFound("scenario revision for computation run was not found")

        current_max = session.execute(
            select(func.max(PlanRevision.revision_no)).where(
                PlanRevision.organization_id == organization_id,
                PlanRevision.scenario_revision_id == run.scenario_revision_id,
            )
        ).scalar_one()
        revision_no = int(current_max or 0) + 1
        plan_revision_id = uuid.uuid4()
        snapshot_id = uuid.uuid4()

        session.add(
            PlanRevision(
                id=plan_revision_id,
                organization_id=organization_id,
                scenario_revision_id=run.scenario_revision_id,
                computation_run_id=computation_run_id,
                parent_plan_revision_id=None,
                revision_no=revision_no,
                source_kind="computed",
                semantic_layer=result.semantic_layer.value,
                engine_id=result.engine_id,
                engine_version=result.engine_version,
                input_fingerprint=result.input_fingerprint,
                output_fingerprint=result.output_fingerprint,
            )
        )

        trip_ids: list[uuid.UUID] = []
        for sequence_no, trip in enumerate(result.trips, start=1):
            trip_id = uuid.uuid4()
            trip_ids.append(trip_id)
            session.add(
                PlannedTrip(
                    id=trip_id,
                    organization_id=organization_id,
                    plan_revision_id=plan_revision_id,
                    sequence_no=sequence_no,
                    direction_key=trip.direction_key,
                    legacy_direction_number=trip.legacy_direction_number,
                    departure_service_minute=trip.departure_service_minute,
                    arrival_service_minute=trip.arrival_service_minute,
                    virtual_departure_service_minute=trip.virtual_departure_service_minute,
                    virtual_arrival_service_minute=trip.virtual_arrival_service_minute,
                    trip_type=trip.trip_type,
                    is_express=trip.is_express,
                    vehicle_block_no=trip.vehicle_block,
                    service_level=trip.service_level,
                )
            )

        for block_no, indexes in sorted(result.vehicle_blocks.items()):
            block_trips = [result.trips[index] for index in indexes]
            session.add(
                VehicleBlock(
                    organization_id=organization_id,
                    plan_revision_id=plan_revision_id,
                    block_no=block_no,
                    trip_count=len(indexes),
                    first_departure_service_minute=(
                        block_trips[0].departure_service_minute if block_trips else None
                    ),
                    last_arrival_service_minute=(
                        block_trips[-1].arrival_service_minute if block_trips else None
                    ),
                )
            )
            for position_no, trip_index in enumerate(indexes, start=1):
                session.add(
                    VehicleBlockTrip(
                        organization_id=organization_id,
                        plan_revision_id=plan_revision_id,
                        block_no=block_no,
                        position_no=position_no,
                        planned_trip_id=trip_ids[trip_index],
                    )
                )

        metrics = result.metrics
        session.add(
            ResultSnapshot(
                id=snapshot_id,
                organization_id=organization_id,
                plan_revision_id=plan_revision_id,
                computation_run_id=computation_run_id,
                output_fingerprint=result.output_fingerprint,
                total_passengers=metrics.total_passengers,
                total_trips=metrics.total_trips,
                mean_extension_km=metrics.mean_extension_km,
                total_distance_km=metrics.total_distance_km,
                effective_fleet=metrics.effective_fleet,
                mean_daily_distance_per_vehicle_km=metrics.mean_daily_distance_per_vehicle_km,
                mean_passengers_per_trip=metrics.mean_passengers_per_trip,
                mean_critical_passengers_per_trip=metrics.mean_critical_passengers_per_trip,
                mean_occupancy_rate=metrics.mean_occupancy_rate,
                passengers_per_km=metrics.passengers_per_km,
                daily_total_cost=metrics.daily_total_cost,
                mean_cost_per_vehicle=metrics.mean_cost_per_vehicle,
                cost_per_trip=metrics.cost_per_trip,
                cost_per_equivalent_passenger=metrics.cost_per_equivalent_passenger,
                mean_trips_per_vehicle=metrics.mean_trips_per_vehicle,
                mean_travel_time_min=metrics.mean_travel_time_min,
                mean_speed_kmh=metrics.mean_speed_kmh,
                distance_semantics=metrics.distance_semantics,
                provenance_notes=list(result.provenance_notes),
            )
        )
        session.commit()

    return load_planning_result(organization_id, computation_run_id)


def load_planning_result(
    organization_id: uuid.UUID,
    computation_run_id: uuid.UUID,
) -> PersistedPlanningResult:
    session_factory = get_session_factory()
    with session_factory() as session:
        plan = session.execute(
            select(PlanRevision).where(
                PlanRevision.organization_id == organization_id,
                PlanRevision.computation_run_id == computation_run_id,
            )
        ).scalar_one_or_none()
        if plan is None:
            raise PlanningResultNotFound("no persisted plan result exists for computation run")

        snapshot = session.execute(
            select(ResultSnapshot).where(
                ResultSnapshot.organization_id == organization_id,
                ResultSnapshot.plan_revision_id == plan.id,
                ResultSnapshot.computation_run_id == computation_run_id,
            )
        ).scalar_one_or_none()
        if snapshot is None:
            raise PlanningResultIntegrityError("plan revision has no result snapshot")

        trip_rows = session.execute(
            select(PlannedTrip)
            .where(
                PlannedTrip.organization_id == organization_id,
                PlannedTrip.plan_revision_id == plan.id,
            )
            .order_by(PlannedTrip.sequence_no)
        ).scalars().all()
        trips = tuple(
            PlannedTripResult(
                direction_key=row.direction_key,
                legacy_direction_number=row.legacy_direction_number,
                departure_service_minute=row.departure_service_minute,
                arrival_service_minute=row.arrival_service_minute,
                virtual_departure_service_minute=row.virtual_departure_service_minute,
                virtual_arrival_service_minute=row.virtual_arrival_service_minute,
                trip_type=row.trip_type,
                is_express=row.is_express,
                vehicle_block=row.vehicle_block_no,
                service_level=row.service_level,
            )
            for row in trip_rows
        )
        trip_index_by_id = {row.id: index for index, row in enumerate(trip_rows)}

        block_rows = session.execute(
            select(VehicleBlockTrip)
            .where(
                VehicleBlockTrip.organization_id == organization_id,
                VehicleBlockTrip.plan_revision_id == plan.id,
            )
            .order_by(VehicleBlockTrip.block_no, VehicleBlockTrip.position_no)
        ).scalars().all()
        blocks: dict[int, list[int]] = {}
        for row in block_rows:
            if row.planned_trip_id not in trip_index_by_id:
                raise PlanningResultIntegrityError("vehicle block references a missing planned trip")
            blocks.setdefault(row.block_no, []).append(trip_index_by_id[row.planned_trip_id])

        metrics = PlanningMetricsResult(
            total_passengers=snapshot.total_passengers,
            total_trips=snapshot.total_trips,
            mean_extension_km=snapshot.mean_extension_km,
            total_distance_km=snapshot.total_distance_km,
            effective_fleet=snapshot.effective_fleet,
            mean_daily_distance_per_vehicle_km=snapshot.mean_daily_distance_per_vehicle_km,
            mean_passengers_per_trip=snapshot.mean_passengers_per_trip,
            mean_critical_passengers_per_trip=snapshot.mean_critical_passengers_per_trip,
            mean_occupancy_rate=snapshot.mean_occupancy_rate,
            passengers_per_km=snapshot.passengers_per_km,
            daily_total_cost=snapshot.daily_total_cost,
            mean_cost_per_vehicle=snapshot.mean_cost_per_vehicle,
            cost_per_trip=snapshot.cost_per_trip,
            cost_per_equivalent_passenger=snapshot.cost_per_equivalent_passenger,
            mean_trips_per_vehicle=snapshot.mean_trips_per_vehicle,
            mean_travel_time_min=snapshot.mean_travel_time_min,
            mean_speed_kmh=snapshot.mean_speed_kmh,
            distance_semantics=snapshot.distance_semantics,
        )
        result = PlanningResult(
            semantic_layer=SemanticLayer(plan.semantic_layer),
            engine_id=plan.engine_id,
            engine_version=plan.engine_version,
            input_fingerprint=plan.input_fingerprint,
            output_fingerprint=plan.output_fingerprint,
            trips=trips,
            effective_fleet=snapshot.effective_fleet,
            vehicle_blocks={number: tuple(indexes) for number, indexes in blocks.items()},
            metrics=metrics,
            provenance_notes=tuple(snapshot.provenance_notes or []),
        )

        if snapshot.output_fingerprint != plan.output_fingerprint:
            raise PlanningResultIntegrityError("plan and result snapshot output fingerprints differ")
        if snapshot.total_trips != len(trips):
            raise PlanningResultIntegrityError("result snapshot trip count differs from persisted trips")
        _validate_blocks(result)
        if planning_result_fingerprint(result) != plan.output_fingerprint:
            raise PlanningResultIntegrityError("persisted planning result fingerprint does not reconstruct exactly")

        return PersistedPlanningResult(
            plan_revision_id=plan.id,
            result_snapshot_id=snapshot.id,
            revision_no=plan.revision_no,
            planning_result=result,
        )
