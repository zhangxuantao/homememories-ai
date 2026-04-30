# backend/tests/test_quality_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.database import get_connection, init_db


@pytest.fixture
def quality_app(tmp_path, monkeypatch):
    """Creates a FastAPI app with a seeded temp database for quality endpoints."""
    db_path = str(tmp_path / "metadata.db")
    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path / "media"))
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("THUMBNAIL_SIZE", "300")

    init_db(db_path)

    # Seed media: two blurry, two with similar dhash (duplicates), one clean
    conn = get_connection(db_path)
    conn.execute(
        """INSERT INTO media (path, filename, media_type, date_added, is_blurry, blur_score)
           VALUES (?,?,?,?,?,?)""",
        ("/a.jpg", "blurry1.jpg", "image", "2026-04-29T10:00:00", 1, 45.0),
    )
    conn.execute(
        """INSERT INTO media (path, filename, media_type, date_added, is_blurry, blur_score)
           VALUES (?,?,?,?,?,?)""",
        ("/b.jpg", "blurry2.jpg", "image", "2026-04-29T11:00:00", 1, 30.0),
    )
    conn.execute(
        """INSERT INTO media (path, filename, media_type, date_added, is_blurry, blur_score)
           VALUES (?,?,?,?,?,?)""",
        ("/c.jpg", "sharp.jpg", "image", "2026-04-29T12:00:00", 0, 500.0),
    )
    conn.execute(
        """INSERT INTO media (path, filename, media_type, date_added, dhash)
           VALUES (?,?,?,?,?)""",
        ("/d.jpg", "dup1.jpg", "image", "2026-04-29T13:00:00", "abcd000000000000"),
    )
    conn.execute(
        """INSERT INTO media (path, filename, media_type, date_added, dhash)
           VALUES (?,?,?,?,?)""",
        ("/e.jpg", "dup2.jpg", "image", "2026-04-29T14:00:00", "abcd000000000000"),
    )
    conn.commit()
    conn.close()

    from app.main import create_app

    app = create_app()
    return app


# ── GET /cleanup/blurry ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_blurry_media_with_results(quality_app):
    """GET /api/admin/cleanup/blurry returns blurry media list."""
    transport = ASGITransport(app=quality_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/admin/cleanup/blurry")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2
    filenames = [item["filename"] for item in data]
    assert "blurry1.jpg" in filenames
    assert "blurry2.jpg" in filenames
    assert "sharp.jpg" not in filenames


@pytest.mark.asyncio
async def test_get_blurry_media_with_threshold(quality_app):
    """GET /api/admin/cleanup/blurry with threshold filters by score."""
    transport = ASGITransport(app=quality_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Only blur_score < 40 (blurry2 has 30, blurry1 has 45)
        resp = await client.get("/api/admin/cleanup/blurry?threshold=40.0&limit=50")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["filename"] == "blurry2.jpg"


@pytest.mark.asyncio
async def test_get_blurry_media_limit(quality_app):
    """GET /api/admin/cleanup/blurry with limit returns at most N items."""
    transport = ASGITransport(app=quality_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/admin/cleanup/blurry?limit=1")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1


# ── GET /cleanup/duplicates ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_duplicates_with_pairs(quality_app):
    """GET /api/admin/cleanup/duplicates returns duplicate pairs."""
    transport = ASGITransport(app=quality_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/admin/cleanup/duplicates")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1  # one pair
    pair = data[0]
    assert len(pair) == 2
    filenames = [pair[0]["filename"], pair[1]["filename"]]
    assert "dup1.jpg" in filenames
    assert "dup2.jpg" in filenames


# ── DELETE /cleanup/blurry ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_blurry_media(quality_app):
    """DELETE /api/admin/cleanup/blurry deletes specified media."""
    transport = ASGITransport(app=quality_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.request(
            "DELETE",
            "/api/admin/cleanup/blurry",
            json=[1, 2],
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "deleted" in data
    assert len(data["deleted"]) == 2

    # Check that media 1 was deleted
    deleted_1 = [d for d in data["deleted"] if d["id"] == 1][0]
    assert deleted_1["deleted"] is True

    # Verify media 1 is gone via API
    async with AsyncClient(transport=transport, base_url="http://test") as client2:
        resp2 = await client2.get("/api/admin/cleanup/blurry")
    remaining = resp2.json()
    remaining_ids = [item["id"] for item in remaining]
    assert 1 not in remaining_ids


@pytest.mark.asyncio
async def test_delete_blurry_media_nonexistent(quality_app):
    """DELETE with nonexistent ID returns deleted=False for that ID."""
    transport = ASGITransport(app=quality_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.request(
            "DELETE",
            "/api/admin/cleanup/blurry",
            json=[999],
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["deleted"][0]["id"] == 999
    assert data["deleted"][0]["deleted"] is False


# ── POST /cleanup/blurry/check ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_post_blur_check_starts_job(quality_app):
    """POST /api/admin/cleanup/blurry/check starts a blur check job."""
    transport = ASGITransport(app=quality_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/admin/cleanup/blurry/check")
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    assert data["status"] in ("pending", "running")


# ── POST /cleanup/duplicates/check ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_post_duplicate_check_starts_job(quality_app):
    """POST /api/admin/cleanup/duplicates/check starts a duplicate check job."""
    transport = ASGITransport(app=quality_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/admin/cleanup/duplicates/check")
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    assert data["status"] in ("pending", "running")
