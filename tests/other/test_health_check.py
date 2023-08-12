from fastapi.testclient import TestClient

from src.main import app
from tests.conftest import mock_logging_config

client = TestClient(app)


def test_health_check_endpoint(mock_logging_config):
    response = client.get("/healthcheck/")

    assert response.status_code == 200
    assert response.json() == {"result": "You've successfully checked your health!"}
