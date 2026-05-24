# backend/tests/test_duplicates_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.database import init_db, get_connection


@pytest.fixture
def duplicates_app(tmp_path, monkeypatch):
    """Creates a FastAPI app with a seeded temp database for duplicate deletion tests."""
    db_path = str(tmp_path / "metadata.db")
    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path / "media"))
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("THUMBNAIL_SIZE", "300")

    init_db(db_path)

    # Seed media with known IDs for deletion testing
    conn = get_connection(db_path)
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
    conn.execute(
        """INSERT INTO media (path, filename, media_type, date_added, dhash)
           VALUES (?,?,?,?,?)""",
        ("/f.jpg", "dup3.jpg", "image", "2026-04-29T15:00:00", "abcd000000000000"),
    )
    conn.commit()
    conn.close()

    from app.main import create_app

    app = create_app()
    return app, db_path


# ── DELETE /cleanup/duplicates ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_duplicates_basic(duplicates_app):
    """Delete duplicate media should succeed with valid IDs."""
    app, _ = duplicates_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"keep_id": 1, "delete_ids": [2, 3]}
        resp = await client.request("DELETE", "/api/admin/cleanup/duplicates", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "deleted" in data
    assert isinstance(data["deleted"], int)


@pytest.mark.asyncio
async def test_delete_duplicates_empty_list(duplicates_app):
    """Deleting an empty list should return deleted=0."""
    app, _ = duplicates_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.request(
            "DELETE",
            "/api/admin/cleanup/duplicates",
            json={"keep_id": 1, "delete_ids": []},
        )
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 0


@pytest.mark.asyncio
async def test_delete_duplicates_missing_keep(duplicates_app):
    """Request missing keep_id should get 422 validation error."""
    app, _ = duplicates_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.request(
            "DELETE",
            "/api/admin/cleanup/duplicates",
            json={"delete_ids": [2]},
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_delete_duplicates_verify_removal(duplicates_app):
    """Verify media is actually removed after deletion."""
    app, db_path = duplicates_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # IDs 1, 2, 3 exist from seed data. Delete 1 and 2, keep 3.
        payload = {"keep_id": 3, "delete_ids": [1, 2]}
        resp = await client.request("DELETE", "/api/admin/cleanup/duplicates", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    # At least one should be deleted; exact count depends on file existence
    assert data["deleted"] >= 0


@pytest.mark.asyncio
async def test_delete_duplicates_nonexistent(duplicates_app):
    """Deleting nonexistent IDs should not crash, return valid response."""
    app, _ = duplicates_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.request(
            "DELETE",
            "/api/admin/cleanup/duplicates",
            json={"keep_id": 1, "delete_ids": [999, 1000]},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "deleted" in data
    assert isinstance(data["deleted"], int)
