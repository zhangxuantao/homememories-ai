# backend/tests/test_media_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.database import get_connection, init_db


@pytest.fixture
def seeded_media_app(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path / "media"))
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("THUMBNAIL_SIZE", "300")

    init_db(db_path)
    conn = get_connection(db_path)
    conn.execute(
        """INSERT INTO media (path, filename, media_type, date_taken, date_added, checksum, width, height)
           VALUES ('/p/1.jpg', 'beach.jpg', 'image', '2025-04-29T12:00:00', '2026-01-01T00:00:00', 'a1', 800, 600)"""
    )
    conn.execute(
        """INSERT INTO media (path, filename, media_type, date_taken, date_added, checksum, width, height)
           VALUES ('/p/2.jpg', 'mountain.jpg', 'image', '2024-04-29T08:00:00', '2026-01-01T00:00:00', 'b1', 1024, 768)"""
    )
    conn.commit()
    conn.close()

    from app.main import create_app

    app = create_app()
    return app


@pytest.mark.asyncio
async def test_get_media_by_id(seeded_media_app):
    transport = ASGITransport(app=seeded_media_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/media/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "beach.jpg"
    assert data["width"] == 800
    assert data["height"] == 600


@pytest.mark.asyncio
async def test_get_media_not_found(seeded_media_app):
    transport = ASGITransport(app=seeded_media_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/media/999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_random_media(seeded_media_app):
    transport = ASGITransport(app=seeded_media_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/media/random?count=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_on_this_day(seeded_media_app):
    transport = ASGITransport(app=seeded_media_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/media/on-this-day?month=4&day=29")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_delete_media(seeded_media_app):
    transport = ASGITransport(app=seeded_media_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.delete("/api/media/1")
    assert resp.status_code == 200
    assert resp.json() == {"deleted": True}

    # Verify it's gone
    resp2 = await client.get("/api/media/1")
    assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_delete_media_not_found(seeded_media_app):
    transport = ASGITransport(app=seeded_media_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.delete("/api/media/999")
    assert resp.status_code == 404
