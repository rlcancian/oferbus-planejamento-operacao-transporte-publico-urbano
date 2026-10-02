from fastapi.testclient import TestClient

from oferbus_api.main import app


def test_health_endpoint() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "service": "oferbus-api",
        "status": "ok",
        "version": "0.1.0",
    }
