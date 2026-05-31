# backend/tests/test_albums.py
import pytest
import os
from fastapi.testclient import TestClient
from app.database import init_db, get_connection
from app.main import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a TestClient with an isolated temp database and seeded data."""
    media_dir = str(tmp_path / "media")
    os.makedirs(media_dir, exist_ok=True)
    monkeypatch.setenv("MEDIA_ROOT", media_dir)
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("THUMBNAIL_SIZE", "300")

    # Initialize DB schema in the temp directory
    init_db()

    # Seed test data
    conn = get_connection()
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_added) VALUES (?, ?, ?, ?, ?)",
        (1, "/test/img1.jpg", "img1.jpg", "image", "2026-01-01T00:00:00"),
    )
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_added) VALUES (?, ?, ?, ?, ?)",
        (2, "/test/img2.jpg", "img2.jpg", "image", "2026-01-02T00:00:00"),
    )
    conn.execute(
        "INSERT INTO albums (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (1, "测试相册", "2026-01-01T00:00:00", "2026-01-01T00:00:00"),
    )
    conn.execute(
        "INSERT INTO album_media (album_id, media_id, sort_order) VALUES (?, ?, ?)",
        (1, 1, 0),
    )
    conn.commit()
    conn.close()

    app = create_app()
    return TestClient(app)


def test_get_album(client):
    resp = client.get("/api/albums/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "测试相册"
    assert data["media_count"] == 1
    assert "cover_thumbnail" in data


def test_get_album_not_found(client):
    resp = client.get("/api/albums/999")
    assert resp.status_code == 404


def test_patch_album_rename(client):
    resp = client.patch("/api/albums/1", json={"name": "重命名相册"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "重命名相册"

    # Verify persisted
    get_resp = client.get("/api/albums/1")
    assert get_resp.json()["name"] == "重命名相册"


def test_patch_album_change_cover(client):
    resp = client.patch("/api/albums/1", json={"cover_media_id": 1})
    assert resp.status_code == 200
    assert resp.json()["cover_media_id"] == 1


def test_patch_album_both(client):
    resp = client.patch("/api/albums/1", json={"name": "新名字", "cover_media_id": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "新名字"
    assert data["cover_media_id"] == 2


def test_patch_album_not_found(client):
    resp = client.patch("/api/albums/999", json={"name": "x"})
    assert resp.status_code == 404


def test_delete_album(client):
    resp = client.delete("/api/albums/1")
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 1

    # Verify gone
    get_resp = client.get("/api/albums/1")
    assert get_resp.status_code == 404


def test_delete_album_not_found(client):
    resp = client.delete("/api/albums/999")
    assert resp.status_code == 404
