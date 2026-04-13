import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.chunking import build_chunks
from app.services.reporting import build_report_prompt
from app.services.retrieval import retrieve_top_chunks

FIXTURES = Path(__file__).parent / "fixtures"


def test_chunking_to_report_prompt_integration():
    """End-to-end: load fixture pages -> chunk -> retrieve -> build prompt."""
    pages = json.loads((FIXTURES / "sample_course_page.json").read_text())

    # Chunk all pages
    chunks = build_chunks(pages)
    assert len(chunks) == 3  # one chunk per page (short texts)

    # Retrieve relevant chunks
    retrieved = retrieve_top_chunks("What are derivatives?", chunks, top_k=2)
    assert len(retrieved) == 2

    # Build report prompt
    prompt = build_report_prompt("Explain derivatives", retrieved)
    assert "Explain derivatives" in prompt
    assert "Limits" in prompt  # from page 1 chunk


def test_upload_and_job_tracking_integration(tmp_path, monkeypatch):
    """End-to-end: upload document -> get job id -> check job status."""
    monkeypatch.setenv("FILE_STORAGE_ROOT", str(tmp_path))
    client = TestClient(app)

    # Upload
    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("test.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert upload_res.status_code == 202
    body = upload_res.json()
    job_id = body["job_id"]

    # Check job status
    status_res = client.get(f"/api/jobs/{job_id}")
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "queued"


def test_report_section_endpoint_integration():
    """End-to-end: call section report endpoint."""
    client = TestClient(app)
    res = client.post(
        "/api/reports/section",
        json={"query": "Explain limits", "document_id": "dummy-id"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Explain limits"
    assert "Explain limits" in data["body"]
