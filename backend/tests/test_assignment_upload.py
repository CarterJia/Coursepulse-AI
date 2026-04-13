from fastapi.testclient import TestClient

from app.main import app


def test_assignment_upload_queues_diagnosis_job(tmp_path, monkeypatch):
    monkeypatch.setenv("FILE_STORAGE_ROOT", str(tmp_path))
    client = TestClient(app)
    response = client.post(
        "/api/assignments/upload",
        files={"file": ("quiz1.png", b"fake-image", "image/png")},
    )
    assert response.status_code == 202
    assert response.json()["status"] == "queued"
