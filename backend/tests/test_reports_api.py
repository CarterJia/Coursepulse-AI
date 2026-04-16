from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.models.report import Report


@patch("app.api.routes.reports.generate_chapter_report")
@patch("app.api.routes.reports.retrieve_top_chunks")
def test_section_report_endpoint_calls_gpt4o(mock_retrieve, mock_generate):
    mock_retrieve.return_value = [{"text": "Limits define continuity", "page_number": 1}]
    mock_generate.return_value = "# Limits\n\nExpanded explanation."

    db = MagicMock()
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    response = client.post(
        "/api/reports/section",
        json={"query": "Explain limits", "document_id": str(uuid4())},
    )
    assert response.status_code == 200
    data = response.json()
    assert "title" in data
    assert "body" in data
    app.dependency_overrides.clear()
