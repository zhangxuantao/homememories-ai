# backend/tests/test_search_api.py
import io
import os
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport
from PIL import Image

from app.database import get_connection, init_db


# ---------------------------------------------------------------------------
# Helper: create a mock EmbeddingPipeline
# ---------------------------------------------------------------------------
def _make_mock_pipeline(embed_images_return=None, embed_text_return=None):
    mock = MagicMock()
    mock.dim = 512
    if embed_images_return is not None:
        mock.embed_images.return_value = embed_images_return
    if embed_text_return is not None:
        mock.embed_text.return_value = embed_text_return
    return mock


# ---------------------------------------------------------------------------
# Helper: seed media + embeddings and build FAISS index
# ---------------------------------------------------------------------------
def _seed_media_and_embeddings(db_path):
    """Insert media rows and embeddings, return (id1, id2, id3)."""
    conn = get_connection(db_path)

    cur = conn.execute(
        """INSERT INTO media (path, filename, media_type, date_taken, date_added, checksum, width, height)
           VALUES ('/p/1.jpg', 'beach.jpg', 'image', '2025-04-29T12:00:00', '2026-01-01T00:00:00', 'a1', 800, 600)"""
    )
    id1 = cur.lastrowid
    cur = conn.execute(
        """INSERT INTO media (path, filename, media_type, date_taken, date_added, checksum, width, height)
           VALUES ('/p/2.jpg', 'mountain.jpg', 'image', '2024-04-29T08:00:00', '2026-01-01T00:00:00', 'b1', 1024, 768)"""
    )
    id2 = cur.lastrowid
    cur = conn.execute(
        """INSERT INTO media (path, filename, media_type, date_taken, date_added, checksum, width, height)
           VALUES ('/p/3.jpg', 'sunset.jpg', 'image', '2023-04-29T18:00:00', '2026-01-01T00:00:00', 'c1', 1200, 900)"""
    )
    id3 = cur.lastrowid

    # Create normalized embedding vectors (3 media x 512 dim)
    v1 = np.random.randn(512).astype(np.float32)
    v1 = v1 / (np.linalg.norm(v1) + 1e-8)
    v2 = np.random.randn(512).astype(np.float32)
    v2 = v2 / (np.linalg.norm(v2) + 1e-8)
    v3 = np.random.randn(512).astype(np.float32)
    v3 = v3 / (np.linalg.norm(v3) + 1e-8)

    for media_id, vec in [(id1, v1), (id2, v2), (id3, v3)]:
        cur = conn.execute(
            "INSERT INTO embeddings (media_id, vector, model_version, created_at) VALUES (?, ?, ?, ?)",
            (media_id, vec.tobytes(), "chinese-clip-vit-base-patch16", "2026-01-01T00:00:00"),
        )
        emb_id = cur.lastrowid
        conn.execute("UPDATE media SET embedding_id = ? WHERE id = ?", (emb_id, media_id))

    conn.commit()
    conn.close()
    return id1, id2, id3


# ---------------------------------------------------------------------------
# Fixture: search app with seeded data and built FAISS index
# ---------------------------------------------------------------------------
@pytest.fixture
def search_app(tmp_path, monkeypatch):
    db_path = str(tmp_path / "metadata.db")
    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path / "media"))
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("THUMBNAIL_SIZE", "300")

    init_db(db_path)
    _seed_media_and_embeddings(db_path)

    # Build FAISS index using real embeddings (mock pipeline for dim only)
    mock_pipeline = _make_mock_pipeline()
    pipe_patcher = patch(
        "app.services.search_service.get_embedding_pipeline",
        return_value=mock_pipeline,
    )
    pipe_patcher.start()
    try:
        from app.services.search_service import rebuild_index
        rebuild_index(db_path)
    finally:
        pipe_patcher.stop()

    # Create app (search router NOT mounted yet — will 404)
    from app.main import create_app
    app = create_app()
    return app


# ---------------------------------------------------------------------------
# Fixture: query vector for mocking search queries
# ---------------------------------------------------------------------------
@pytest.fixture
def query_vec():
    """Normalized random query vector for mock pipeline."""
    vec = np.random.randn(1, 512).astype(np.float32)
    return vec / (np.linalg.norm(vec) + 1e-8)


# ---------------------------------------------------------------------------
# Test: text search - 200 OK
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_text_search(search_app, query_vec):
    """POST /api/search/text returns search results.

    NOTE: This test will 404 until the search router is mounted in main.py (Task 10).
    """
    mock_pipeline = _make_mock_pipeline(embed_text_return=query_vec)
    with patch(
        "app.services.search_service.get_embedding_pipeline",
        return_value=mock_pipeline,
    ):
        transport = ASGITransport(app=search_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/search/text", json={
                "query": "beach sunset",
                "limit": 2,
            })
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert "next_cursor" in data
    assert len(data["results"]) <= 2
    for item in data["results"]:
        assert "id" in item
        assert "filename" in item


# ---------------------------------------------------------------------------
# Test: text search - empty query returns 422
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_text_search_empty_query(search_app, query_vec):
    """POST /api/search/text with empty query returns 422.

    NOTE: This test will 404 until the search router is mounted in main.py (Task 10).
    """
    mock_pipeline = _make_mock_pipeline(embed_text_return=query_vec)
    with patch(
        "app.services.search_service.get_embedding_pipeline",
        return_value=mock_pipeline,
    ):
        transport = ASGITransport(app=search_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/search/text", json={
                "query": "   ",
                "limit": 5,
            })
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Test: image search - 200 OK
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_image_search(search_app, query_vec):
    """POST /api/search/image returns search results for uploaded image.

    NOTE: This test will 404 until the search router is mounted in main.py (Task 10).
    """
    # Create a test image as bytes
    img = Image.new("RGB", (64, 64), color=(100, 200, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    mock_pipeline = _make_mock_pipeline(embed_images_return=query_vec)
    with patch(
        "app.services.search_service.get_embedding_pipeline",
        return_value=mock_pipeline,
    ):
        transport = ASGITransport(app=search_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/search/image", files={
                "image_file": ("test.jpg", img_bytes, "image/jpeg"),
            })
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert isinstance(data["results"], list)
