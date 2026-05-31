import pytest
import io as io_module
from fastapi.testclient import TestClient
from PIL import Image
from app.main import app
from app.database import get_connection, init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path))

    init_db()

    # Create test images
    img1_path = tmp_path / "img1.jpg"
    img2_path = tmp_path / "img2.jpg"
    Image.new("RGB", (200, 150), color="red").save(img1_path, "JPEG")
    Image.new("RGB", (300, 200), color="blue").save(img2_path, "JPEG")

    conn = get_connection()
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_added) VALUES (?, ?, ?, ?, ?)",
        (1, str(img1_path), "img1.jpg", "image", "2026-01-01T00:00:00"),
    )
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_added) VALUES (?, ?, ?, ?, ?)",
        (2, str(img2_path), "img2.jpg", "image", "2026-01-02T00:00:00"),
    )
    conn.commit()
    conn.close()

    yield


def test_collage_grid():
    resp = client.post("/api/media/collage", json={"media_ids": [1, 2], "layout": "grid"})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"
    img = Image.open(io_module.BytesIO(resp.content))
    assert img.width > 0 and img.height > 0


def test_collage_horizontal():
    resp = client.post("/api/media/collage", json={"media_ids": [1, 2], "layout": "horizontal"})
    assert resp.status_code == 200
    img = Image.open(io_module.BytesIO(resp.content))
    assert img.height <= 400


def test_collage_vertical():
    resp = client.post("/api/media/collage", json={"media_ids": [1, 2], "layout": "vertical"})
    assert resp.status_code == 200
    img = Image.open(io_module.BytesIO(resp.content))
    assert img.width <= 400


def test_collage_default_layout():
    resp = client.post("/api/media/collage", json={"media_ids": [1]})
    assert resp.status_code == 200


def test_collage_empty():
    resp = client.post("/api/media/collage", json={"media_ids": []})
    assert resp.status_code == 400


def test_collage_nonexistent_media():
    resp = client.post("/api/media/collage", json={"media_ids": [999]})
    assert resp.status_code == 404
