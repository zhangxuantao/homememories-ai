# backend/tests/test_curation.py
import pytest
import os
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from app.database import get_connection, init_db


@pytest.fixture
def curation_app(tmp_path, monkeypatch):
    media_dir = str(tmp_path / "media")
    os.makedirs(media_dir, exist_ok=True)
    monkeypatch.setenv("MEDIA_ROOT", media_dir)
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))

    init_db()
    now = datetime.now()
    month = now.strftime("%Y-%m")
    now_iso = now.isoformat()

    conn = get_connection()
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_taken, date_added, blur_score, is_blurry) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (1, "/test/a.jpg", "a.jpg", "image", f"{month}-01", now_iso, 800, False),
    )
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_taken, date_added, blur_score, is_blurry) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (2, "/test/b.jpg", "b.jpg", "image", f"{month}-15", now_iso, 200, False),
    )
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_taken, date_added, blur_score, is_blurry) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (3, "/test/c.jpg", "c.jpg", "image", f"{month}-20", now_iso, 100, True),
    )
    conn.execute(
        "INSERT INTO face_clusters (id, label, photo_count) VALUES (?, ?, ?)",
        (1, "Person A", 1),
    )
    conn.execute(
        "INSERT INTO faces (id, media_id, cluster_id, bbox) VALUES (?, ?, ?, ?)",
        (1, 1, 1, '[0,0,100,100]'),
    )
    conn.commit()
    conn.close()

    from app.main import create_app
    return create_app()


@pytest.mark.asyncio
async def test_generate_curation(curation_app):
    month = datetime.now().strftime("%Y-%m")
    transport = ASGITransport(app=curation_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/admin/curate/generate", json={"month": month})
    assert resp.status_code == 200
    data = resp.json()
    assert data["month"] == month
    assert data["count"] > 0


@pytest.mark.asyncio
async def test_get_curation(curation_app):
    month = datetime.now().strftime("%Y-%m")
    transport = ASGITransport(app=curation_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/admin/curate/generate", json={"month": month})
        resp = await client.get(f"/api/admin/curate?month={month}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) > 0
    # Photo 1 should be top (sharp + has face)
    assert data["items"][0]["id"] == 1


@pytest.mark.asyncio
async def test_generate_empty_month(curation_app):
    transport = ASGITransport(app=curation_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/admin/curate/generate", json={"month": "2020-01"})
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


@pytest.mark.asyncio
async def test_get_empty_curation(curation_app):
    transport = ASGITransport(app=curation_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/admin/curate?month=2020-01")
    assert resp.status_code == 200
    assert resp.json()["items"] == []
