from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.middleware.byok import BYOKMiddleware


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(BYOKMiddleware)

    @app.get("/echo")
    def echo(request: Request):
        return {"key": request.state.user_api_key}

    return app


def test_byok_header_populates_request_state():
    client = TestClient(_build_app())
    resp = client.get("/echo", headers={"X-User-API-Key": "sk-user"})
    assert resp.status_code == 200
    assert resp.json() == {"key": "sk-user"}


def test_byok_header_absent_sets_none():
    client = TestClient(_build_app())
    resp = client.get("/echo")
    assert resp.status_code == 200
    assert resp.json() == {"key": None}


def test_byok_header_empty_string_is_none():
    client = TestClient(_build_app())
    resp = client.get("/echo", headers={"X-User-API-Key": ""})
    assert resp.status_code == 200
    assert resp.json() == {"key": None}
