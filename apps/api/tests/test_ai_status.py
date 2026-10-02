from fastapi.testclient import TestClient

from oferbus_api.main import app


def test_ai_status_is_provider_neutral_and_disallows_direct_sql(monkeypatch) -> None:
    monkeypatch.delenv("OFERBUS_AI_PROVIDER", raising=False)
    monkeypatch.delenv("OFERBUS_AI_MODEL", raising=False)

    response = TestClient(app).get("/ai/status")

    assert response.status_code == 200
    assert response.json() == {
        "boundary": "ready",
        "provider": "unconfigured",
        "configured": False,
        "model": None,
        "direct_sql_allowed": False,
    }
