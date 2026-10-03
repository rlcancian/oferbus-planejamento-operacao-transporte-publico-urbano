from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
import uuid

from dev_seed import (
    ORGANIZATION_ID,
    PLANNING_SCENARIO_REVISION_ID,
    PROJECT_ID,
    SCENARIO_REVISION_ID,
    SUBJECT,
)


def request_json(method: str, url: str, *, body: dict | None = None, authenticated: bool = False) -> tuple[int, object]:
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if authenticated:
        headers.update({"X-OferBus-Subject": SUBJECT, "X-OferBus-Organization-Id": str(ORGANIZATION_ID), "X-Correlation-Id": "phase-c-integration-smoke"})
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
            if status == 200 and isinstance(payload, dict) and payload.get("status") == "ok": return
        except Exception as exc:
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
        if payload.get("status") in {"succeeded", "failed", "cancelled"}: break
        time.sleep(0.25)
    if not isinstance(final, dict) or final.get("status") != "succeeded": raise RuntimeError(f"Computation did not succeed: {final}")
    if final.get("progress_percent") != 100: raise RuntimeError(f"Computation progress did not reach 100: {final}")
    return final


def main() -> None:
    parser = argparse.ArgumentParser(description="Run OferBus integrated platform and persisted planning smoke")
    parser.add_argument("--api-url", default="http://127.0.0.1:8010")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args(); api_url = args.api_url.rstrip("/"); smoke_token = uuid.uuid4().hex
    wait_for_api(api_url, args.timeout)
    _, ready = request_json("GET", f"{api_url}/ready"); assert isinstance(ready, dict) and ready.get("status") == "ready", ready; assert ready.get("migration") == "0006_plan_editing", ready
    _, identity = request_json("GET", f"{api_url}/identity/me", authenticated=True); assert isinstance(identity, dict) and identity.get("organization_id") == str(ORGANIZATION_ID), identity
    _, planning = request_json("GET", f"{api_url}/planning/scenario-revisions/{PLANNING_SCENARIO_REVISION_ID}/input", authenticated=True); assert isinstance(planning, dict), planning
    planning_input_fingerprint = planning["input_fingerprint"]; planning_input = planning["planning_input"]; assert planning_input["semantic_layer"] == "normalized"; assert len(planning_input["directions"]) == 1
    _, ai_status = request_json("GET", f"{api_url}/ai/status"); assert isinstance(ai_status, dict) and ai_status.get("boundary") == "ready" and ai_status.get("direct_sql_allowed") is False
    _, tools = request_json("GET", f"{api_url}/ai/tools", authenticated=True); names = {tool.get("name") for tool in tools if isinstance(tool, dict)}; assert "computations.submit_platform_smoke" in names; assert not any(name in names for name in {"sql", "shell", "http.request"})
    _, execution = request_json("POST", f"{api_url}/ai/tools/computations.submit_platform_smoke/execute", authenticated=True, body={"confirmed": True, "arguments": {"scenario_revision_id": str(SCENARIO_REVISION_ID), "idempotency_key": f"phase-c-platform-smoke-{smoke_token}", "message": "Phase C platform regression smoke passed", "delay_seconds": 0.1}})
    output = execution["output"]; platform_final = wait_for_run(api_url, output["run_id"], args.timeout)
    _, planning_run = request_json("POST", f"{api_url}/computations", authenticated=True, body={"scenario_revision_id": str(PLANNING_SCENARIO_REVISION_ID), "run_kind": "core-planning", "idempotency_key": f"phase-c-core-planning-{smoke_token}", "max_attempts": 2})
    planning_run_id = planning_run["run_id"]; planning_final = wait_for_run(api_url, planning_run_id, args.timeout); output_fingerprint = planning_final["output_fingerprint"]; diagnostics = planning_final["diagnostics"]
    _, persisted = request_json("GET", f"{api_url}/results/computations/{planning_run_id}", authenticated=True); assert persisted["plan_revision_id"] == diagnostics["plan_revision_id"]
    context = persisted["context"]; assert context["project_id"] == str(PROJECT_ID); assert context["lines"][0]["public_code"] == "DEV-001"
    assert len(persisted["trips"]) == diagnostics["trip_count"]; assert len(persisted["vehicle_blocks"]) == diagnostics["effective_fleet"]
    plan_revision_id = persisted["plan_revision_id"]
    _, march = request_json("GET", f"{api_url}/plans/{plan_revision_id}/march", authenticated=True); assert march["source_kind"] == "computed"; assert march["service_start_minute"] == 60; assert len(march["trips"]) == diagnostics["trip_count"]
    march_trips = march["trips"]; first_trip = march_trips[0]; original_departure = first_trip["departure_service_minute"]; original_arrival = first_trip["arrival_service_minute"]

    # C.3: a temporal edit creates a child revision, shifts actual+virtual times by
    # one integer delta, and leaves the computed parent byte-for-byte observable.
    command_id = str(uuid.uuid4())
    move_body = {"client_command_id": command_id, "command_type": "move-trip", "reason": "C.3 integration smoke temporal move", "trip_sequence_no": first_trip["sequence_no"], "departure_service_minute": original_departure - 1}
    _, edited = request_json("POST", f"{api_url}/plans/{plan_revision_id}/edits", authenticated=True, body=move_body); assert edited["parent_plan_revision_id"] == plan_revision_id; assert edited["command_type"] == "move-trip"
    child_id = edited["derived_plan_revision_id"]
    _, edited_again = request_json("POST", f"{api_url}/plans/{plan_revision_id}/edits", authenticated=True, body=move_body); assert edited_again["derived_plan_revision_id"] == child_id
    _, child_march = request_json("GET", f"{api_url}/plans/{child_id}/march", authenticated=True); assert child_march["source_kind"] == "manual"; assert child_march["parent_plan_revision_id"] == plan_revision_id
    child_first = child_march["trips"][0]; assert child_first["departure_service_minute"] == original_departure - 1; assert child_first["arrival_service_minute"] == original_arrival - 1
    assert child_first["virtual_departure_service_minute"] == first_trip["virtual_departure_service_minute"] - 1; assert child_first["virtual_arrival_service_minute"] == first_trip["virtual_arrival_service_minute"] - 1
    _, parent_after = request_json("GET", f"{api_url}/plans/{plan_revision_id}/march", authenticated=True); assert parent_after == march

    _, latest = request_json("GET", f"{api_url}/results/latest", authenticated=True); assert latest["computation_run_id"] == planning_run_id; assert latest["output_fingerprint"] == output_fingerprint
    print(json.dumps({"status":"pass","migration":ready["migration"],"organization_id":str(ORGANIZATION_ID),"planning_run_id":planning_run_id,"plan_revision_id":plan_revision_id,"temporal_child_plan_revision_id":child_id,"temporal_parent_immutable":True,"planning_trip_count":diagnostics["trip_count"],"planning_effective_fleet":diagnostics["effective_fleet"],"platform_run_id":platform_final["run_id"],"ai_boundary":ai_status["boundary"]}, sort_keys=True))


if __name__ == "__main__": main()
