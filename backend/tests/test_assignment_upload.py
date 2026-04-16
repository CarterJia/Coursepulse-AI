from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


@patch("app.services.diagnosis.create_job")
def test_assignment_upload_queues_diagnosis_job(mock_create_job, tmp_path, monkeypatch):
    monkeypatch.setenv("FILE_STORAGE_ROOT", str(tmp_path))
    mock_create_job.return_value = str(uuid4())
    client = TestClient(app)
    response = client.post(
        "/api/assignments/upload",
        files={"file": ("quiz1.png", b"fake-image", "image/png")},
    )
    assert response.status_code == 202
    assert response.json()["status"] == "queued"
