from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select

from oferbus_core import fingerprint
from oferbus_db import (
    LineDirection,
    ObservedTripDataset,
    ObservedTripDatasetRevision,
    ObservedTripObservation,
    get_session_factory,
)

from .application import (
    DatasetRevisionCreated,
    DirectionObservationBatch,
    PlanningInputError,
    PlanningInputNotFound,
    _direction_payload,
)


@dataclass(frozen=True)
class CreateObservedDatasetRevisionCommand:
    organization_id: uuid.UUID
    created_by: uuid.UUID | None
    dataset_id: uuid.UUID
    parent_revision_id: uuid.UUID | None
    source_label: str | None
    source_metadata: dict | None
    directions: tuple[DirectionObservationBatch, ...]


def create_observed_dataset_revision(
    command: CreateObservedDatasetRevisionCommand,
) -> DatasetRevisionCreated:
    if not command.directions:
        raise PlanningInputError("dataset revision requires at least one direction")
    if len({item.direction_id for item in command.directions}) != len(command.directions):
        raise PlanningInputError("dataset revision contains duplicate direction ids")
    if any(not item.observations for item in command.directions):
        raise PlanningInputError("every dataset direction requires at least one observation")

    revision_id = uuid.uuid4()
    session_factory = get_session_factory()
    with session_factory() as session:
        dataset = session.execute(
            select(ObservedTripDataset)
            .where(
                ObservedTripDataset.organization_id == command.organization_id,
                ObservedTripDataset.id == command.dataset_id,
            )
            .with_for_update()
        ).scalar_one_or_none()
        if dataset is None:
            raise PlanningInputNotFound("observed dataset not found in active organization")

        if command.parent_revision_id is not None:
            parent = session.execute(
                select(ObservedTripDatasetRevision).where(
                    ObservedTripDatasetRevision.organization_id == command.organization_id,
                    ObservedTripDatasetRevision.id == command.parent_revision_id,
                    ObservedTripDatasetRevision.dataset_id == command.dataset_id,
                )
            ).scalar_one_or_none()
            if parent is None:
                raise PlanningInputNotFound("parent dataset revision not found")

        for batch in command.directions:
            direction = session.execute(
                select(LineDirection).where(
                    LineDirection.organization_id == command.organization_id,
                    LineDirection.id == batch.direction_id,
                    LineDirection.line_id == dataset.line_id,
                )
            ).scalar_one_or_none()
            if direction is None:
                raise PlanningInputNotFound("line direction not found for dataset line")

        current_max = session.execute(
            select(func.max(ObservedTripDatasetRevision.revision_no)).where(
                ObservedTripDatasetRevision.organization_id == command.organization_id,
                ObservedTripDatasetRevision.dataset_id == command.dataset_id,
            )
        ).scalar_one()
        revision_no = int(current_max or 0) + 1

        payload = {
            "line_id": str(dataset.line_id),
            "directions": [
                _direction_payload(item)
                for item in sorted(command.directions, key=lambda item: str(item.direction_id))
            ],
        }
        content_fingerprint = fingerprint(payload)

        session.add(
            ObservedTripDatasetRevision(
                id=revision_id,
                organization_id=command.organization_id,
                dataset_id=command.dataset_id,
                revision_no=revision_no,
                parent_revision_id=command.parent_revision_id,
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
        dataset_id=command.dataset_id,
        dataset_revision_id=revision_id,
        revision_no=revision_no,
        content_fingerprint=content_fingerprint,
    )
