import pytest
import os
from httpx import AsyncClient, ASGITransport
from app.database import get_connection, init_db


@pytest.fixture
def favorites_app(tmp_path, monkeypatch):
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
async def test_toggle_favorite_add_then_remove(favorites_app):
    transport = ASGITransport(app=favorites_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Add favorite
        resp = await client.post("/api/favorites/1")
        assert resp.status_code == 200
        assert resp.json() == {"favorited": True}

        # Toggle again — should remove
        resp = await client.post("/api/favorites/1")
        assert resp.status_code == 200
        assert resp.json() == {"favorited": False}


@pytest.mark.asyncio
async def test_list_favorites(favorites_app):
    transport = ASGITransport(app=favorites_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Favorite media id 1
        await client.post("/api/favorites/1")

        resp = await client.get("/api/favorites")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) >= 1
        assert items[0]["id"] == 1
        assert "fav_created_at" in items[0]


@pytest.mark.asyncio
async def test_check_favorites(favorites_app):
    transport = ASGITransport(app=favorites_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Favorite only media id 1
        await client.post("/api/favorites/1")

        resp = await client.get("/api/favorites/check?ids=1,2,999")
        assert resp.status_code == 200
        data = resp.json()
        assert data["1"] is True
        assert data["2"] is False
        assert data["999"] is False


@pytest.mark.asyncio
async def test_recent_favorites(favorites_app):
    transport = ASGITransport(app=favorites_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Favorite both media
        await client.post("/api/favorites/1")
        await client.post("/api/favorites/2")

        resp = await client.get("/api/favorites/recent?limit=3")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) <= 3
        assert len(items) == 2
