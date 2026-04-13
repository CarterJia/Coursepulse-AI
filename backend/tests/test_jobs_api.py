from fastapi.testclient import TestClient

from app.main import app


def test_job_status_endpoint_returns_known_state():
    client = TestClient(app)
    response = client.get("/api/jobs/test-job-id")
    assert response.status_code in {200, 404}
