from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.models.course import Course
from app.models.document import Document
from app.models.job import Job


def _mock_db():
    db = MagicMock()
    course = MagicMock(spec=Course)
    course.id = uuid4()
    db.query.return_value.filter.return_value.first.return_value = course
    return db


def test_document_upload_creates_record_and_job(tmp_path, monkeypatch):
    monkeypatch.setenv("FILE_STORAGE_ROOT", str(tmp_path))
    db = _mock_db()
    app.dependency_overrides[get_db] = lambda: db
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
    # Verify db.add was called (Document + Job)
    assert db.add.call_count >= 2
    app.dependency_overrides.clear()
