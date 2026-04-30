# backend/tests/test_search_service.py
import os
import time
import json
import sqlite3
import hashlib
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
import io

from app.database import get_connection, init_db


def _seed_media_for_embeddings(db_path):
    """Insert two test media rows and return their IDs."""
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
    conn.commit()
    conn.close()
    return id1, id2


# ---------------------------------------------------------------------------
# Helper: mock pipeline with dim=512 and configurable embedding return values
# ---------------------------------------------------------------------------
def _make_mock_pipeline(embed_images_return=None, embed_text_return=None):
    """Create a MagicMock simulating EmbeddingPipeline."""
    mock = MagicMock()
    mock.dim = 512
    if embed_images_return is not None:
        mock.embed_images.return_value = embed_images_return
    if embed_text_return is not None:
        mock.embed_text.return_value = embed_text_return
    return mock


# ---------------------------------------------------------------------------
# 1. test_generate_embeddings_job
# ---------------------------------------------------------------------------
def test_generate_embeddings_job(tmp_db_path):
    """generate_embeddings starts a job, populates embeddings table, updates media.embedding_id."""
    id1, id2 = _seed_media_for_embeddings(tmp_db_path)

    # Create fake embedding vectors (2 images x 512 dim)
    fake_vectors = np.array([
        np.random.randn(512).astype(np.float32),
        np.random.randn(512).astype(np.float32),
    ])
    norms = np.linalg.norm(fake_vectors, axis=1, keepdims=True)
    fake_vectors = fake_vectors / (norms + 1e-8)

    mock_pipeline = _make_mock_pipeline(embed_images_return=fake_vectors)

    # Mock SearchIndex to avoid FAISS
    mock_index = MagicMock()
    mock_index.index = "mock"
    mock_index.id_map = []

    # Use start()/stop() so patches survive the background thread
    pipe_patcher = patch(
        "app.services.search_service.get_embedding_pipeline",
        return_value=mock_pipeline,
    )
    index_patcher = patch(
        "app.services.search_service.SearchIndex",
        return_value=mock_index,
    )
    pipe_patcher.start()
    index_patcher.start()
    try:
        from app.services.search_service import generate_embeddings

        job_id = generate_embeddings(tmp_db_path)

        # Poll for completion (background thread)
        from app.services.scan_service import JobTracker
        tracker = JobTracker()
        for _ in range(50):
            job = tracker.get(job_id)
            if job and job["status"] in ("completed", "failed"):
                break
            time.sleep(0.1)
        else:
            pytest.fail("generate_embeddings job did not complete in time")

        assert job["status"] == "completed", f"Job failed: {job.get('error')}"

        # Verify embeddings table
        conn = get_connection(tmp_db_path)
        emb_rows = conn.execute(
            "SELECT id, media_id, vector FROM embeddings ORDER BY media_id"
        ).fetchall()
        assert len(emb_rows) == 2
        assert emb_rows[0]["media_id"] == id1
        assert emb_rows[1]["media_id"] == id2
        # Vectors should be non-empty blobs (float32 * 512 = 2048 bytes)
        assert len(emb_rows[0]["vector"]) == 512 * 4
        assert len(emb_rows[1]["vector"]) == 512 * 4

        # Verify media.embedding_id is set
        media_rows = conn.execute(
            "SELECT id, embedding_id FROM media ORDER BY id"
        ).fetchall()
        assert media_rows[0]["embedding_id"] is not None
        assert media_rows[1]["embedding_id"] is not None
        assert media_rows[0]["embedding_id"] == emb_rows[0]["id"]
        assert media_rows[1]["embedding_id"] == emb_rows[1]["id"]

        # Verify rebuild_index was called (index built and saved)
        mock_index.build.assert_called_once()
        mock_index.save.assert_called_once()

        conn.close()
    finally:
        pipe_patcher.stop()
        index_patcher.stop()

    # Verify we didn't try to load the real CLIP model
    mock_pipeline.embed_images.assert_called_once()


# ---------------------------------------------------------------------------
# 2. test_generate_embeddings_skips_existing
# ---------------------------------------------------------------------------
def test_generate_embeddings_skips_existing(tmp_db_path):
    """Media that already have an embedding_id should be skipped."""
    id1, id2 = _seed_media_for_embeddings(tmp_db_path)

    # Pre-populate embedding for id1 only
    conn = get_connection(tmp_db_path)
    fake_vec = np.random.randn(512).astype(np.float32)
    fake_vec = fake_vec / (np.linalg.norm(fake_vec) + 1e-8)
    cur = conn.execute(
        "INSERT INTO embeddings (media_id, vector, model_version, created_at) VALUES (?, ?, ?, ?)",
        (id1, fake_vec.tobytes(), "chinese-clip-vit-base-patch16", "2026-01-01T00:00:00"),
    )
    emb1_id = cur.lastrowid
    conn.execute("UPDATE media SET embedding_id = ? WHERE id = ?", (emb1_id, id1))
    conn.commit()
    conn.close()

    # Now run generate_embeddings - should only process id2 (no embedding)
    fake_vectors = np.array([
        np.random.randn(512).astype(np.float32),
    ])
    norms = np.linalg.norm(fake_vectors, axis=1, keepdims=True)
    fake_vectors = fake_vectors / (norms + 1e-8)

    mock_pipeline = _make_mock_pipeline(embed_images_return=fake_vectors)
    mock_index = MagicMock()
    mock_index.index = "mock"
    mock_index.id_map = []

    pipe_patcher = patch(
        "app.services.search_service.get_embedding_pipeline",
        return_value=mock_pipeline,
    )
    index_patcher = patch(
        "app.services.search_service.SearchIndex",
        return_value=mock_index,
    )
    pipe_patcher.start()
    index_patcher.start()
    try:
        from app.services.search_service import generate_embeddings

        job_id = generate_embeddings(tmp_db_path)

        # Poll for completion
        from app.services.scan_service import JobTracker
        tracker = JobTracker()
        for _ in range(50):
            job = tracker.get(job_id)
            if job and job["status"] in ("completed", "failed"):
                break
            time.sleep(0.1)
        assert job["status"] == "completed", f"Job failed: {job.get('error')}"

        # pipeline.embed_images should have been called with only id2's path
        call_args = mock_pipeline.embed_images.call_args[0][0]
        assert len(call_args) == 1  # only one path
        assert call_args[0] == "/p/2.jpg"

        # Verify exactly 2 embeddings total (id1's original + id2's new)
        conn = get_connection(tmp_db_path)
        emb_count = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
        assert emb_count == 2
        conn.close()
    finally:
        pipe_patcher.stop()
        index_patcher.stop()


# ---------------------------------------------------------------------------
# 3. test_search_by_text
# ---------------------------------------------------------------------------
def test_search_by_text(tmp_db_path):
    """search_by_text returns paginated results ordered by relevance."""
    id1, id2 = _seed_media_for_embeddings(tmp_db_path)

    # Pre-populate embeddings for both media
    conn = get_connection(tmp_db_path)
    v1 = np.random.randn(512).astype(np.float32)
    v1 = v1 / (np.linalg.norm(v1) + 1e-8)
    v2 = np.random.randn(512).astype(np.float32)
    v2 = v2 / (np.linalg.norm(v2) + 1e-8)

    cur = conn.execute(
        "INSERT INTO embeddings (media_id, vector, model_version, created_at) VALUES (?, ?, ?, ?)",
        (id1, v1.tobytes(), "v1", "2026-01-01T00:00:00"),
    )
    emb1_id = cur.lastrowid
    cur = conn.execute(
        "INSERT INTO embeddings (media_id, vector, model_version, created_at) VALUES (?, ?, ?, ?)",
        (id2, v2.tobytes(), "v1", "2026-01-01T00:00:00"),
    )
    emb2_id = cur.lastrowid
    conn.execute("UPDATE media SET embedding_id = ? WHERE id = ?", (emb1_id, id1))
    conn.execute("UPDATE media SET embedding_id = ? WHERE id = ?", (emb2_id, id2))
    conn.commit()
    conn.close()

    # Mock pipeline for rebuild_index (needs dim) and for search
    query_vec = np.random.randn(1, 512).astype(np.float32)
    query_vec = query_vec / (np.linalg.norm(query_vec) + 1e-8)
    mock_pipeline = _make_mock_pipeline(embed_text_return=query_vec)

    pipe_patcher = patch(
        "app.services.search_service.get_embedding_pipeline",
        return_value=mock_pipeline,
    )
    pipe_patcher.start()
    try:
        from app.services.search_service import rebuild_index, search_by_text

        # Rebuild index with real embeddings
        rebuild_index(tmp_db_path)

        # First page: limit=1
        result = search_by_text("beach", limit=1, cursor=0, db_path=tmp_db_path)

        assert "results" in result
        assert "next_cursor" in result
        assert len(result["results"]) == 1
        assert result["next_cursor"] == "1"

        # Second page
        result2 = search_by_text("beach", limit=1, cursor=1, db_path=tmp_db_path)
        assert len(result2["results"]) == 1
        # Should be no more pages (only 2 items total)
        assert result2["next_cursor"] is None
    finally:
        pipe_patcher.stop()


# ---------------------------------------------------------------------------
# 4. test_search_by_image
# ---------------------------------------------------------------------------
def test_search_by_image(tmp_db_path):
    """search_by_image returns results for uploaded image bytes."""
    id1, id2 = _seed_media_for_embeddings(tmp_db_path)

    # Pre-populate embeddings
    conn = get_connection(tmp_db_path)
    v1 = np.random.randn(512).astype(np.float32)
    v1 = v1 / (np.linalg.norm(v1) + 1e-8)
    v2 = np.random.randn(512).astype(np.float32)
    v2 = v2 / (np.linalg.norm(v2) + 1e-8)

    cur = conn.execute(
        "INSERT INTO embeddings (media_id, vector, model_version, created_at) VALUES (?, ?, ?, ?)",
        (id1, v1.tobytes(), "v1", "2026-01-01T00:00:00"),
    )
    emb1_id = cur.lastrowid
    cur = conn.execute(
        "INSERT INTO embeddings (media_id, vector, model_version, created_at) VALUES (?, ?, ?, ?)",
        (id2, v2.tobytes(), "v1", "2026-01-01T00:00:00"),
    )
    emb2_id = cur.lastrowid
    conn.execute("UPDATE media SET embedding_id = ? WHERE id = ?", (emb1_id, id1))
    conn.execute("UPDATE media SET embedding_id = ? WHERE id = ?", (emb2_id, id2))
    conn.commit()
    conn.close()

    # Create a test image as bytes
    img = Image.new("RGB", (64, 64), color=(100, 200, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    # Mock pipeline to return a known query vector
    query_vec = np.random.randn(1, 512).astype(np.float32)
    query_vec = query_vec / (np.linalg.norm(query_vec) + 1e-8)
    mock_pipeline = _make_mock_pipeline(embed_images_return=query_vec)

    pipe_patcher = patch(
        "app.services.search_service.get_embedding_pipeline",
        return_value=mock_pipeline,
    )
    pipe_patcher.start()
    try:
        from app.services.search_service import rebuild_index, search_by_image

        rebuild_index(tmp_db_path)

        results = search_by_image(img_bytes, limit=2, db_path=tmp_db_path)

        assert isinstance(results, list)
        assert len(results) >= 1
        # Each result should be a MediaItem-like object with required fields
        for item in results:
            assert hasattr(item, "id")
            assert hasattr(item, "filename")
    finally:
        pipe_patcher.stop()


# ---------------------------------------------------------------------------
# 5. test_search_by_text_cache_hit
# ---------------------------------------------------------------------------
def test_search_by_text_cache_hit(tmp_db_path):
    """search_by_text should use cache on repeated identical queries."""
    id1, id2 = _seed_media_for_embeddings(tmp_db_path)

    # Pre-populate embeddings
    conn = get_connection(tmp_db_path)
    v1 = np.random.randn(512).astype(np.float32)
    v1 = v1 / (np.linalg.norm(v1) + 1e-8)
    v2 = np.random.randn(512).astype(np.float32)
    v2 = v2 / (np.linalg.norm(v2) + 1e-8)

    conn.execute(
        "INSERT INTO embeddings (media_id, vector, model_version, created_at) VALUES (?, ?, ?, ?)",
        (id1, v1.tobytes(), "v1", "2026-01-01T00:00:00"),
    )
    conn.execute(
        "INSERT INTO embeddings (media_id, vector, model_version, created_at) VALUES (?, ?, ?, ?)",
        (id2, v2.tobytes(), "v1", "2026-01-01T00:00:00"),
    )
    conn.execute(
        "UPDATE media SET embedding_id = (SELECT id FROM embeddings WHERE media_id = ?) WHERE id = ?",
        (id1, id1),
    )
    conn.execute(
        "UPDATE media SET embedding_id = (SELECT id FROM embeddings WHERE media_id = ?) WHERE id = ?",
        (id2, id2),
    )
    conn.commit()
    conn.close()

    query_vec = np.random.randn(1, 512).astype(np.float32)
    query_vec = query_vec / (np.linalg.norm(query_vec) + 1e-8)
    mock_pipeline = _make_mock_pipeline(embed_text_return=query_vec)

    pipe_patcher = patch(
        "app.services.search_service.get_embedding_pipeline",
        return_value=mock_pipeline,
    )
    pipe_patcher.start()
    try:
        from app.services.search_service import rebuild_index, search_by_text

        rebuild_index(tmp_db_path)

        # First call - should embed and search
        result1 = search_by_text("sunset beach", limit=20, cursor=0, db_path=tmp_db_path)
        first_call_count = mock_pipeline.embed_text.call_count

        # Second call with same query - should use cache
        result2 = search_by_text("sunset beach", limit=20, cursor=0, db_path=tmp_db_path)
        # embed_text should NOT have been called again
        assert mock_pipeline.embed_text.call_count == first_call_count

        # Results should be identical
        ids1 = [r.id for r in result1["results"]]
        ids2 = [r.id for r in result2["results"]]
        assert ids1 == ids2
    finally:
        pipe_patcher.stop()


# ---------------------------------------------------------------------------
# 6. test_rebuild_index_empty
# ---------------------------------------------------------------------------
def test_rebuild_index_empty(tmp_db_path):
    """rebuild_index with no embeddings should create an empty but valid index."""
    # Create media without embeddings
    _seed_media_for_embeddings(tmp_db_path)

    mock_pipeline = _make_mock_pipeline()

    pipe_patcher = patch(
        "app.services.search_service.get_embedding_pipeline",
        return_value=mock_pipeline,
    )
    pipe_patcher.start()
    try:
        from app.services.search_service import rebuild_index

        rebuild_index(tmp_db_path)

        # Index files should still be created (empty index)
        from app.config import settings
        faiss_dir = settings.faiss_dir
        assert os.path.exists(os.path.join(faiss_dir, "index.faiss"))
        assert os.path.exists(os.path.join(faiss_dir, "id_map.json"))
    finally:
        pipe_patcher.stop()
