# backend/tests/test_import_photos.py
import os
import io
import zipfile
import tempfile
from fastapi.testclient import TestClient
from PIL import Image
from app.main import app

client = TestClient(app)


def _create_test_zip(contents: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in contents.items():
            zf.writestr(name, data)
    buf.seek(0)
    return buf.read()


def test_import_takeout_empty_zip(monkeypatch):
    monkeypatch.setenv("MEDIA_ROOT", tempfile.mkdtemp())
    monkeypatch.setenv("DATA_ROOT", tempfile.mkdtemp())
    monkeypatch.setenv("PORT", "0")

    zip_data = _create_test_zip({"readme.txt": b"hello"})
    resp = client.post(
        "/api/import/takeout",
        files={"file": ("test.zip", io.BytesIO(zip_data), "application/zip")},
    )
    assert resp.status_code == 400
    assert "未找到照片" in resp.json()["detail"]


def test_import_takeout_with_images(monkeypatch):
    media_root = tempfile.mkdtemp()
    monkeypatch.setenv("MEDIA_ROOT", media_root)
    monkeypatch.setenv("DATA_ROOT", tempfile.mkdtemp())
    monkeypatch.setenv("PORT", "0")

    img1 = io.BytesIO()
    Image.new("RGB", (100, 100), "red").save(img1, "JPEG")
    img1.seek(0)

    img2 = io.BytesIO()
    Image.new("RGB", (200, 200), "blue").save(img2, "JPEG")
    img2.seek(0)

    zip_data = _create_test_zip({
        "photos/img1.jpg": img1.read(),
        "photos/img2.jpg": img2.read(),
        "photos/metadata.json": b'{"title":"test"}',
    })

    resp = client.post(
        "/api/import/takeout",
        files={"file": ("takeout.zip", io.BytesIO(zip_data), "application/zip")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 2
    assert "takeout_" in data["destination"]


def test_import_takeout_not_zip(monkeypatch):
    monkeypatch.setenv("MEDIA_ROOT", tempfile.mkdtemp())
    monkeypatch.setenv("DATA_ROOT", tempfile.mkdtemp())

    resp = client.post(
        "/api/import/takeout",
        files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert resp.status_code == 400


def test_import_icloud_dir_not_found(monkeypatch):
    monkeypatch.setenv("MEDIA_ROOT", tempfile.mkdtemp())
    monkeypatch.setenv("DATA_ROOT", tempfile.mkdtemp())
    monkeypatch.setenv("PORT", "0")

    resp = client.post("/api/import/icloud", json={"source_dir": "/nonexistent/path/xyz"})
    assert resp.status_code == 400


def test_import_icloud_with_images(monkeypatch):
    media_root = tempfile.mkdtemp()
    source_dir = tempfile.mkdtemp()
    monkeypatch.setenv("MEDIA_ROOT", media_root)
    monkeypatch.setenv("DATA_ROOT", tempfile.mkdtemp())
    monkeypatch.setenv("PORT", "0")

    Image.new("RGB", (100, 100), "red").save(os.path.join(source_dir, "photo1.jpg"), "JPEG")
    Image.new("RGB", (200, 200), "blue").save(os.path.join(source_dir, "photo2.png"), "PNG")
    with open(os.path.join(source_dir, ".DS_Store"), "w") as f:
        f.write("skip me")

    resp = client.post("/api/import/icloud", json={"source_dir": source_dir})
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 2
    assert "icloud_" in data["destination"]
