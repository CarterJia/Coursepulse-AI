import json
import uuid
from pathlib import Path
from unittest.mock import MagicMock, call, patch

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
def test_upload_dispatches_background_task(mock_pipeline, tmp_path, monkeypatch):
    monkeypatch.setenv("FILE_STORAGE_ROOT", str(tmp_path))
    db = MagicMock()
    mock_course = MagicMock()
    mock_course.id = uuid.uuid4()
    db.query.return_value.filter.return_value.first.return_value = mock_course

    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    res = client.post(
        "/api/documents/upload",
        files={"file": ("t.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert res.status_code == 202
    body = res.json()
    assert "document_id" in body and body["document_id"]
    assert "job_id" in body and body["job_id"]
    app.dependency_overrides.clear()


@patch("app.services.ingestion.run_report_pipeline")
@patch("app.services.ingestion.extract_images")
@patch("app.services.ingestion.extract_pages")
@patch("app.services.ingestion.extract_glossary")
def test_ingestion_pipeline_calls_new_reporting(
    mock_glossary, mock_pages, mock_images, mock_report, tmp_path, monkeypatch
):
    """run_ingestion_pipeline must call extract_images, then run_report_pipeline
    (not the old generate_chapter_report loop)."""
    from app.services.ingestion import _derived_dir, run_ingestion_pipeline

    monkeypatch.setenv("FILE_STORAGE_ROOT", str(tmp_path))
    mock_pages.return_value = [{"page_number": 1, "text": "hi"}]
    mock_images.return_value = {}
    mock_glossary.return_value = []

    # Use a manager mock to verify call ordering between extract_images and
    # run_report_pipeline.
    manager = MagicMock(name="manager")
    manager.attach_mock(mock_images, "extract_images")
    manager.attach_mock(mock_report, "run_report_pipeline")

    # Patch SessionLocal to a controllable mock
    with patch("app.services.ingestion.SessionLocal") as mock_session_cls, \
         patch("app.services.ingestion.generate_embedding") as mock_emb:
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        pdf_path = str(tmp_path / "x.pdf")
        mock_db.get.return_value = MagicMock(
            file_path=pdf_path,
            filename="x.pdf",
        )
        mock_emb.return_value = [0.0] * 512

        doc_id = uuid.uuid4()
        job_id = uuid.uuid4()
        run_ingestion_pipeline(doc_id, job_id)

        # Assert extract_images was called with the correct pdf_path and derived dir
        mock_images.assert_called_once_with(pdf_path, _derived_dir(doc_id))

        # Assert run_report_pipeline was called with exactly the right arguments
        mock_report.assert_called_once_with(
            mock_db, doc_id, mock_pages.return_value, mock_images.return_value
        )

        # Assert extract_images was called BEFORE run_report_pipeline
        images_index = next(
            i for i, c in enumerate(manager.mock_calls)
            if c == call.extract_images(pdf_path, _derived_dir(doc_id))
        )
        report_index = next(
            i for i, c in enumerate(manager.mock_calls)
            if c == call.run_report_pipeline(
                mock_db, doc_id, mock_pages.return_value, mock_images.return_value
            )
        )
        assert images_index < report_index, (
            "extract_images must be called before run_report_pipeline"
        )
