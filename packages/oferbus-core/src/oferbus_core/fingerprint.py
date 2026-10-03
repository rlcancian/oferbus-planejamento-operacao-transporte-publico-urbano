from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _canonical(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, float):
        if not (value == value and abs(value) != float("inf")):
            raise ValueError("fingerprints do not accept NaN or infinite floats")
        return value
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_canonical(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    payload = canonical_json(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def planning_result_payload(result: Any) -> dict[str, Any]:
    """Return the canonical material identity of a planning result.

    The persisted/output fingerprint deliberately excludes the fingerprint field
    itself so the same function can verify a reconstructed immutable result.
    """

    return {
        "semantic_layer": result.semantic_layer,
        "engine_id": result.engine_id,
        "engine_version": result.engine_version,
        "input_fingerprint": result.input_fingerprint,
        "trips": result.trips,
        "effective_fleet": result.effective_fleet,
        "vehicle_blocks": result.vehicle_blocks,
        "metrics": result.metrics,
        "provenance_notes": result.provenance_notes,
    }


def planning_result_fingerprint(result: Any) -> str:
    return fingerprint(planning_result_payload(result))
