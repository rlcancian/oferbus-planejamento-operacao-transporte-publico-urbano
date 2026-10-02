from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request

from dev_seed import (
    ORGANIZATION_ID,
    PLANNING_SCENARIO_REVISION_ID,
    SCENARIO_REVISION_ID,
    SUBJECT,
)


def request_json(
    method: str,
    url: str,
    *,
    body: dict | None = None,
    authenticated: bool = False,
) -> tuple[int, object]:
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if authenticated:
        headers.update(
            {
                "X-OferBus-Subject": SUBJECT,
                "X-OferBus-Organization-Id": str(ORGANIZATION_ID),
                "X-Correlation-Id": "phase-b-integration-smoke",
            }
        )

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = response.read().decode("utf-8")
            return response.status, json.loads(payload) if payload else {}
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8")
        raise RuntimeError(f"HTTP {exc.code} {url}: {payload}") from exc


def wait_for_api(api_url: str, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            status, payload = request_json("GET", f"{api_url}/health")
            if status == 200 and isinstance(payload, dict) and payload.get("status") == "ok":
                return
        except Exception as exc:  # service startup polling
            last_error = exc
        time.sleep(0.5)
    raise RuntimeError(f"API did not become healthy: {last_error}")


def wait_for_run(api_url: str, run_id: str, timeout: float) -> dict:
    deadline = time.monotonic() + timeout
    final: dict | None = None
    while time.monotonic() < deadline:
        _, payload = request_json("GET", f"{api_url}/computations/{run_id}", authenticated=True)
        assert isinstance(payload, dict), payload
        final = payload
        if payload.get("status") in {"succeeded", "failed", "cancelled"}:
            break
        time.sleep(0.25)
    if not isinstance(final, dict) or final.get("status") != "succeeded":
        raise RuntimeError(f"Computation did not succeed: {final}")
    if final.get("progress_percent") != 100:
        raise RuntimeError(f"Computation progress did not reach 100: {final}")
    return final


def main() -> None:
    parser = argparse.ArgumentParser(description="Run OferBus integrated platform and deterministic planning smoke")
    parser.add_argument("--api-url", default="http://127.0.0.1:8010")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()
    api_url = args.api_url.rstrip("/")

    wait_for_api(api_url, args.timeout)

    _, ready = request_json("GET", f"{api_url}/ready")
    assert isinstance(ready, dict) and ready.get("status") == "ready", ready
    assert ready.get("migration") == "0004_planning_inputs", ready

    _, identity = request_json("GET", f"{api_url}/identity/me", authenticated=True)
    assert isinstance(identity, dict) and identity.get("organization_id") == str(ORGANIZATION_ID), identity

    _, planning = request_json(
        "GET",
        f"{api_url}/planning/scenario-revisions/{PLANNING_SCENARIO_REVISION_ID}/input",
        authenticated=True,
    )
    assert isinstance(planning, dict), planning
    assert planning.get("scenario_revision_id") == str(PLANNING_SCENARIO_REVISION_ID), planning
    assert isinstance(planning.get("input_fingerprint"), str) and len(planning["input_fingerprint"]) == 64, planning
    planning_input_fingerprint = planning["input_fingerprint"]
    planning_input = planning.get("planning_input")
    assert isinstance(planning_input, dict), planning
    assert planning_input.get("semantic_layer") == "normalized", planning_input
    directions = planning_input.get("directions")
    assert isinstance(directions, list) and len(directions) == 1, planning_input
    assert directions[0].get("direction_key") == "outbound", directions
    assert len(directions[0].get("observations", [])) == 3, directions

    # Retain the Phase A AI/platform smoke as a regression check.
    _, ai_status = request_json("GET", f"{api_url}/ai/status")
    assert isinstance(ai_status, dict) and ai_status.get("boundary") == "ready", ai_status
    assert ai_status.get("direct_sql_allowed") is False, ai_status

    _, tools = request_json("GET", f"{api_url}/ai/tools", authenticated=True)
    assert isinstance(tools, list), tools
    names = {tool.get("name") for tool in tools if isinstance(tool, dict)}
    assert "computations.submit_platform_smoke" in names, names
    assert not any(name in names for name in {"sql", "shell", "http.request"}), names

    _, execution = request_json(
        "POST",
        f"{api_url}/ai/tools/computations.submit_platform_smoke/execute",
        authenticated=True,
        body={
            "confirmed": True,
            "arguments": {
                "scenario_revision_id": str(SCENARIO_REVISION_ID),
                "idempotency_key": "phase-b3-platform-smoke-v1",
                "message": "Phase B3 platform regression smoke passed",
                "delay_seconds": 0.1,
            },
        },
    )
    assert isinstance(execution, dict), execution
    output = execution.get("output")
    assert isinstance(output, dict) and isinstance(output.get("run_id"), str), execution
    platform_final = wait_for_run(api_url, output["run_id"], args.timeout)

    # Submit the first real deterministic planning computation. No scientific
    # payload is accepted here: all input is loaded from the immutable revision.
    _, planning_run = request_json(
        "POST",
        f"{api_url}/computations",
        authenticated=True,
        body={
            "scenario_revision_id": str(PLANNING_SCENARIO_REVISION_ID),
            "run_kind": "core-planning",
            "idempotency_key": "phase-b3-core-planning-v1",
            "max_attempts": 2,
        },
    )
    assert isinstance(planning_run, dict), planning_run
    assert planning_run.get("run_kind") == "core-planning", planning_run
    assert planning_run.get("semantic_layer") == "normalized", planning_run
    assert planning_run.get("input_fingerprint") == planning_input_fingerprint, planning_run
    assert planning_run.get("output_fingerprint") is None, planning_run
    planning_run_id = planning_run.get("run_id")
    assert isinstance(planning_run_id, str), planning_run

    planning_final = wait_for_run(api_url, planning_run_id, args.timeout)
    assert planning_final.get("semantic_layer") == "normalized", planning_final
    assert planning_final.get("input_fingerprint") == planning_input_fingerprint, planning_final
    output_fingerprint = planning_final.get("output_fingerprint")
    assert isinstance(output_fingerprint, str) and len(output_fingerprint) == 64, planning_final
    diagnostics = planning_final.get("diagnostics")
    assert isinstance(diagnostics, dict), planning_final
    assert diagnostics.get("handler") == "core-planning", diagnostics
    assert diagnostics.get("semantic_layer") == "normalized", diagnostics
    assert diagnostics.get("input_fingerprint") == planning_input_fingerprint, diagnostics
    assert diagnostics.get("output_fingerprint") == output_fingerprint, diagnostics
    assert isinstance(diagnostics.get("trip_count"), int) and diagnostics["trip_count"] > 0, diagnostics
    assert isinstance(diagnostics.get("effective_fleet"), int) and diagnostics["effective_fleet"] >= 1, diagnostics
    assert diagnostics.get("result_persistence") == "deferred-to-phase-b4", diagnostics

    print(
        json.dumps(
            {
                "status": "pass",
                "migration": ready.get("migration"),
                "organization_id": str(ORGANIZATION_ID),
                "planning_scenario_revision_id": str(PLANNING_SCENARIO_REVISION_ID),
                "planning_input_fingerprint": planning_input_fingerprint,
                "planning_output_fingerprint": output_fingerprint,
                "planning_run_id": planning_run_id,
                "planning_trip_count": diagnostics.get("trip_count"),
                "planning_effective_fleet": diagnostics.get("effective_fleet"),
                "platform_run_id": platform_final.get("run_id"),
                "ai_boundary": ai_status.get("boundary"),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
