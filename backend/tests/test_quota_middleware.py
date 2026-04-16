from datetime import datetime, timezone

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.middleware.quota import QuotaMiddleware, _reset_counter_for_tests


@pytest.fixture(autouse=True)
def _reset():
    _reset_counter_for_tests()
    yield
    _reset_counter_for_tests()


def _build_app(limit: int = 2) -> FastAPI:
    app = FastAPI()
    app.add_middleware(QuotaMiddleware, limit=limit, guarded_path="/api/documents/upload")

    @app.post("/api/documents/upload")
    def upload(request: Request):
        return {"ok": True}

    @app.get("/api/other")
    def other():
        return {"ok": True}

    return app


def test_quota_allows_first_n_requests():
    client = TestClient(_build_app(limit=2))
    assert client.post("/api/documents/upload").status_code == 200
    assert client.post("/api/documents/upload").status_code == 200


def test_quota_blocks_after_limit():
    client = TestClient(_build_app(limit=2))
    client.post("/api/documents/upload")
    client.post("/api/documents/upload")
    resp = client.post("/api/documents/upload")
    assert resp.status_code == 429
    body = resp.json()
    assert body["detail"] == "Daily quota exhausted"
    assert body["use_byok"] is True


def test_quota_only_applies_to_guarded_path():
    client = TestClient(_build_app(limit=0))
    resp = client.get("/api/other")
    assert resp.status_code == 200


def test_quota_skipped_when_byok_present():
    app = FastAPI()
    app.add_middleware(QuotaMiddleware, limit=0, guarded_path="/api/documents/upload")

    @app.middleware("http")
    async def fake_byok(request, call_next):
        request.state.user_api_key = "sk-user"
        return await call_next(request)

    @app.post("/api/documents/upload")
    def upload():
        return {"ok": True}

    client = TestClient(app)
    assert client.post("/api/documents/upload").status_code == 200


def test_quota_response_header_exposes_remaining():
    client = TestClient(_build_app(limit=3))
    resp = client.post("/api/documents/upload")
    assert resp.status_code == 200
    assert resp.headers.get("X-Quota-Remaining") == "2"
