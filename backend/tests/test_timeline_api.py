# backend/tests/test_timeline_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.database import get_connection, init_db


@pytest.fixture
def seeded_timeline_app(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path / "media"))
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("THUMBNAIL_SIZE", "300")

    init_db(db_path)
    conn = get_connection(db_path)
    conn.execute(
        """INSERT INTO media (path, filename, media_type, date_taken, date_added, checksum)
           VALUES ('/p/1.jpg', '1.jpg', 'image', '2025-04-29T12:00:00', '2026-01-01T00:00:00', 'a1')"""
    )
    conn.execute(
        """INSERT INTO media (path, filename, media_type, date_taken, date_added, checksum)
           VALUES ('/p/2.jpg', '2.jpg', 'image', '2025-05-15T08:00:00', '2026-01-01T00:00:00', 'b1')"""
    )
    conn.execute(
        """INSERT INTO media (path, filename, media_type, date_taken, date_added, checksum)
           VALUES ('/p/3.jpg', '3.jpg', 'image', '2024-04-29T10:00:00', '2026-01-01T00:00:00', 'c1')"""
    )
    conn.commit()
    conn.close()

    from app.main import create_app

    app = create_app()
    return app


@pytest.mark.asyncio
async def test_get_years(seeded_timeline_app):
    transport = ASGITransport(app=seeded_timeline_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/timeline/years")
    assert resp.status_code == 200
    years = resp.json()
    assert 2025 in years
    assert 2024 in years


@pytest.mark.asyncio
async def test_get_events_by_year(seeded_timeline_app):
    transport = ASGITransport(app=seeded_timeline_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/timeline/events?year=2025")
    assert resp.status_code == 200
    events = resp.json()
    assert isinstance(events, list)


@pytest.mark.asyncio
async def test_get_events_requires_year(seeded_timeline_app):
    transport = ASGITransport(app=seeded_timeline_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/timeline/events")
    assert resp.status_code == 422  # validation error
