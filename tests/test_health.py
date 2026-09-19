from app.main import app
from fastapi.testclient import TestClient


def test_health_endpoint_returns_api_and_database_status() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "sahachari-api"
    assert body["database"] == "connected"

