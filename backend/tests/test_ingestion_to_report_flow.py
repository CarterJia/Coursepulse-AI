import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.services.chunking import build_chunks

FIXTURES = Path(__file__).parent / "fixtures"


def test_chunking_to_retrieval_integration():
    pages = json.loads((FIXTURES / "sample_course_page.json").read_text())
    chunks = build_chunks(pages)
    assert len(chunks) == 3
    assert all("text" in c for c in chunks)


@patch("app.api.routes.documents.run_ingestion_pipeline")
def test_upload_and_job_tracking_integration(mock_pipeline, tmp_path, monkeypatch):
    monkeypatch.setenv("FILE_STORAGE_ROOT", str(tmp_path))
    db = MagicMock()

    # Mock course lookup
    mock_course = MagicMock()
    mock_course.id = __import__("uuid").uuid4()
    db.query.return_value.filter.return_value.first.return_value = mock_course

    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)

    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("test.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert upload_res.status_code == 202
    body = upload_res.json()
    assert "document_id" in body
    assert "job_id" in body
    app.dependency_overrides.clear()
