# backend/tests/test_admin_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.database import get_connection, init_db


@pytest.fixture
def admin_app(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path / "media"))
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("THUMBNAIL_SIZE", "300")

    init_db(db_path)
    conn = get_connection(db_path)
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added, checksum) VALUES (?,?,?,?,?)",
        ("/a.jpg", "a.jpg", "image", "2026-04-29T10:00:00", "x1"),
    )
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added, checksum) VALUES (?,?,?,?,?)",
        ("/b.mp4", "b.mp4", "video", "2026-04-29T11:00:00", "x2"),
    )
    conn.commit()
    conn.close()

    from app.main import create_app

    app = create_app()
    return app


@pytest.mark.asyncio
async def test_post_scan_starts_job(admin_app):
    transport = ASGITransport(app=admin_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/admin/scan")
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    assert data["status"] in ("pending", "running")


@pytest.mark.asyncio
async def test_get_scan_status(admin_app):
    transport = ASGITransport(app=admin_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Start a scan first
        start_resp = await client.post("/api/admin/scan")
        job_id = start_resp.json()["job_id"]

        resp = await client.get(f"/api/admin/scan/status?job_id={job_id}")
    assert resp.status_code == 200
    assert resp.json()["job_id"] == job_id


@pytest.mark.asyncio
async def test_get_scan_status_not_found(admin_app):
    transport = ASGITransport(app=admin_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/admin/scan/status?job_id=nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_system_stats(admin_app):
    transport = ASGITransport(app=admin_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/admin/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["media_count"] == 2
    assert data["image_count"] == 1
    assert data["video_count"] == 1
    assert data["db_size_bytes"] > 0
