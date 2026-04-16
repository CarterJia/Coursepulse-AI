import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_sample_returns_configured_id(monkeypatch, client):
    sample_id = str(uuid.uuid4())
    monkeypatch.setattr(settings, "sample_document_id", sample_id)
    resp = client.get("/api/documents/sample")
    assert resp.status_code == 200
    assert resp.json() == {"document_id": sample_id}


def test_sample_returns_404_when_unconfigured(monkeypatch, client):
    monkeypatch.setattr(settings, "sample_document_id", "")
    resp = client.get("/api/documents/sample")
    assert resp.status_code == 404
