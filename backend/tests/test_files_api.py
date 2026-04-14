import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_serve_file_returns_bytes(tmp_path, monkeypatch):
    monkeypatch.setenv("FILE_STORAGE_ROOT", str(tmp_path))
    # Need to reimport settings to pick up env; or bypass by patching resolve
    doc_id = uuid.uuid4()
    derived = tmp_path / "derived" / str(doc_id)
    derived.mkdir(parents=True)
    (derived / "page_1_img_0.png").write_bytes(b"PNGDATA")

    # Reload settings
    from app.core import config
    config.settings.file_storage_root = str(tmp_path)

    client = TestClient(app)
    res = client.get(f"/api/files/{doc_id}/page_1_img_0.png")
    assert res.status_code == 200
    assert res.content == b"PNGDATA"
    assert res.headers["content-type"] == "image/png"


def test_serve_file_rejects_path_traversal():
    client = TestClient(app)
    res = client.get(f"/api/files/{uuid.uuid4()}/..%2Fetc%2Fpasswd")
    assert res.status_code == 400


def test_serve_file_rejects_invalid_uuid():
    client = TestClient(app)
    res = client.get("/api/files/not-a-uuid/x.png")
    assert res.status_code == 400


def test_serve_file_404_on_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("FILE_STORAGE_ROOT", str(tmp_path))
    from app.core import config
    config.settings.file_storage_root = str(tmp_path)
    client = TestClient(app)
    res = client.get(f"/api/files/{uuid.uuid4()}/does_not_exist.png")
    assert res.status_code == 404
