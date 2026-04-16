import uuid
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app


def test_document_detail_includes_section_type_in_reports():
    db = MagicMock()
    doc = MagicMock()
    doc.id = uuid.uuid4()
    doc.filename = "x.pdf"
    doc.mime_type = "application/pdf"
    doc.created_at = __import__("datetime").datetime.utcnow()
    db.get.return_value = doc

    r1 = MagicMock(id=uuid.uuid4(), title="课件概览", body="...", section_type="overview")
    r2 = MagicMock(id=uuid.uuid4(), title="矩阵乘法", body="...", section_type="topic")
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [r1, r2]

    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    res = client.get(f"/api/documents/{doc.id}")
    assert res.status_code == 200
    body = res.json()
    assert all("section_type" in r for r in body["reports"])
    section_types = [r["section_type"] for r in body["reports"]]
    assert section_types == ["overview", "topic"]
    app.dependency_overrides.clear()
