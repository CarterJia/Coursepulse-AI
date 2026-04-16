from unittest.mock import MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.models.job import Job


def _mock_db_with_job():
    job_id = uuid4()
    mock_job = MagicMock(spec=Job)
    mock_job.id = job_id
    mock_job.job_type = "ingestion"
    mock_job.status = "queued"
    mock_job.error_message = None

    db = MagicMock()
    db.get.return_value = mock_job
    return db, job_id


def test_job_status_returns_queued():
    db, job_id = _mock_db_with_job()
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    response = client.get(f"/api/jobs/{job_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    app.dependency_overrides.clear()


def test_job_status_returns_404_for_unknown():
    db = MagicMock()
    db.get.return_value = None
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    response = client.get(f"/api/jobs/{uuid4()}")
    assert response.status_code == 404
    app.dependency_overrides.clear()
