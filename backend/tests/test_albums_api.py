import pytest
import os
from httpx import AsyncClient, ASGITransport
from app.database import get_connection, init_db


@pytest.fixture
def albums_app(tmp_path, monkeypatch):
    media_dir = str(tmp_path / "media")
    os.makedirs(media_dir, exist_ok=True)
    monkeypatch.setenv("MEDIA_ROOT", media_dir)
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))

    init_db()
    conn = get_connection()
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_taken, date_added, checksum) "
        "VALUES (1, '/p/1.jpg', 'a.jpg', 'image', '2025-01-01', '2026-01-01', 'a1')"
    )
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_taken, date_added, checksum) "
        "VALUES (2, '/p/2.jpg', 'b.jpg', 'image', '2025-01-02', '2026-01-01', 'b1')"
    )
    conn.commit()
    conn.close()

    from app.main import create_app
    return create_app()


@pytest.mark.asyncio
async def test_create_album(albums_app):
    transport = ASGITransport(app=albums_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/albums", json={"name": "宝宝成长"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "宝宝成长"
    assert "id" in data


@pytest.mark.asyncio
async def test_add_media_to_album(albums_app):
    transport = ASGITransport(app=albums_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        album_resp = await client.post("/api/albums", json={"name": "精选"})
        album_id = album_resp.json()["id"]

        resp = await client.post(f"/api/albums/{album_id}/media", json={"media_ids": [1, 2]})
        assert resp.status_code == 200
        assert resp.json()["added"] == 2


@pytest.mark.asyncio
async def test_get_album_media(albums_app):
    transport = ASGITransport(app=albums_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        album_resp = await client.post("/api/albums", json={"name": "精选"})
        album_id = album_resp.json()["id"]
        await client.post(f"/api/albums/{album_id}/media", json={"media_ids": [1, 2]})

        resp = await client.get(f"/api/albums/{album_id}/media")
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 2


@pytest.mark.asyncio
async def test_album_not_found(albums_app):
    transport = ASGITransport(app=albums_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/albums/999/media", json={"media_ids": [1]})
    assert resp.status_code == 404
