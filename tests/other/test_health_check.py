from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/healthcheck/")

    assert response.status_code == 200
    assert response.json() == {"result": "You've successfully checked your health!"}
