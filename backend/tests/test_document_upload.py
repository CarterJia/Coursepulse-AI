from fastapi.testclient import TestClient

from app.main import app


def test_document_upload_returns_job_payload(tmp_path, monkeypatch):
    monkeypatch.setenv("FILE_STORAGE_ROOT", str(tmp_path))
    client = TestClient(app)
    response = client.post(
        "/api/documents/upload",
        files={"file": ("week1.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert response.status_code == 202
    body = response.json()
    assert "document_id" in body
    assert "job_id" in body
    assert body["status"] == "queued"
