import uuid

from oferbus_core import ObservedTripInput, fingerprint
from oferbus_planning.application import DirectionObservationBatch, _direction_payload


def test_direction_observation_payload_is_stable_and_json_fingerprintable():
    direction_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    batch = DirectionObservationBatch(
        direction_id=direction_id,
        observations=(
            ObservedTripInput(60, 10, critical_passengers=8, travel_time_min=12),
            ObservedTripInput(90, 12, critical_passengers=9, travel_time_min=11),
        ),
    )

    payload = _direction_payload(batch)

    assert payload["direction_id"] == str(direction_id)
    assert payload["observations"][0]["departure_service_minute"] == 60
    assert fingerprint(payload) == fingerprint(payload)
    assert len(fingerprint(payload)) == 64
