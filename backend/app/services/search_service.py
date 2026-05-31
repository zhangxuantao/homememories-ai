# backend/app/services/search_service.py
import os
import json
import hashlib
import threading
import tempfile
import time
from datetime import datetime, timezone

import numpy as np

from app.database import get_connection
from app.models import MediaItem
from app.config import settings
from app.ai.embedding import EmbeddingPipeline
from app.ai.search_index import SearchIndex
from app.services.scan_service import JobTracker

# Module-level lazy singletons
_search_index = None
_search_index_db_path = None
_embedding_pipeline = None

CACHE_TTL_SECONDS = 3600  # 1 hour


def get_search_index(db_path: str | None = None) -> SearchIndex:
    """Lazy-load FAISS SearchIndex from disk, cached per db_path."""
    global _search_index, _search_index_db_path
    path = db_path or settings.db_path

    if _search_index is not None and _search_index_db_path == path:
        return _search_index

    dim = get_embedding_pipeline().dim
    faiss_dir = settings.faiss_dir

    index = SearchIndex(dim=dim)
    if not index.load(faiss_dir):
        # No index on disk yet - return empty index
        _search_index = index
        _search_index_db_path = path
        return _search_index

    _search_index = index
    _search_index_db_path = path
    return _search_index


def get_embedding_pipeline() -> EmbeddingPipeline:
    """Lazy-load EmbeddingPipeline singleton."""
    global _embedding_pipeline
    if _embedding_pipeline is None:
        _embedding_pipeline = EmbeddingPipeline.get_instance()
    return _embedding_pipeline


def _generate_all_embeddings(db_path: str | None = None) -> int:
    """Generate CLIP embeddings for all media without them (synchronous).
    Returns the number of embeddings created.
    """
    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT id, path FROM media "
        "WHERE embedding_id IS NULL AND media_type = 'image' "
        "ORDER BY id"
    ).fetchall()
    conn.close()

    if not rows:
        return 0

    media_ids = [r["id"] for r in rows]
    paths = []
    for r in rows:
        p = r["path"]
        if not os.path.isabs(p):
            p = os.path.join(settings.media_root, p)
        paths.append(p)

    pipeline = get_embedding_pipeline()
    model_version = "chinese-clip-vit-base-patch16"
    now = datetime.now(timezone.utc).isoformat()

    embeddings = pipeline.embed_images(paths, batch_size=32)

    if len(embeddings) != len(paths):
        embeddings_list = []
        valid_media_ids = []
        for i, p in enumerate(paths):
            single_result = pipeline.embed_images([p])
            if single_result.shape[0] == 1:
                embeddings_list.append(single_result[0])
                valid_media_ids.append(media_ids[i])
        embeddings = np.array(embeddings_list, dtype=np.float32) if embeddings_list else np.empty((0, 512), dtype=np.float32)
        media_ids = valid_media_ids

    conn = get_connection(db_path)
    processed = 0
    for i, media_id in enumerate(media_ids):
        if i >= len(embeddings):
            break
        vec = embeddings[i]
        cur = conn.execute(
            "INSERT INTO embeddings (media_id, vector, model_version, created_at) "
            "VALUES (?, ?, ?, ?)",
            (media_id, vec.astype(np.float32).tobytes(), model_version, now),
        )
        emb_id = cur.lastrowid
        conn.execute(
            "UPDATE media SET embedding_id = ? WHERE id = ?",
            (emb_id, media_id),
        )
        processed += 1

    conn.commit()
    conn.close()

    rebuild_index(db_path)

    return processed


def generate_embeddings(db_path: str | None = None) -> str:
    """Start a background job to generate CLIP embeddings for media without them.

    Returns a job_id for tracking progress via JobTracker.
    """
    tracker = JobTracker()
    job_id = tracker.create(total=0, processed=0, stage="embedding")

    def _run():
        tracker.update(job_id, status="running")
        try:
            conn = get_connection(db_path)
            row = conn.execute("SELECT COUNT(*) FROM media WHERE embedding_id IS NULL AND media_type = 'image'").fetchone()
            total = row[0] if row else 0
            conn.close()
            tracker.update(job_id, total=total, processed=0)

            processed = _generate_all_embeddings(db_path)

            tracker.update(job_id, status="completed", progress=100.0,
                           total=total, processed=processed)
        except Exception as e:
            tracker.update(job_id, status="failed", error=str(e))

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return job_id


def rebuild_index(db_path: str | None = None) -> None:
    """Load all embeddings from DB, build FAISS index, save to disk."""
    global _search_index, _search_index_db_path

    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT e.media_id, e.vector FROM embeddings e "
        "JOIN media m ON e.media_id = m.id "
        "ORDER BY e.media_id"
    ).fetchall()
    conn.close()

    embeddings = [(r["media_id"], r["vector"]) for r in rows]

    dim = get_embedding_pipeline().dim
    index = SearchIndex(dim=dim)
    index.build(embeddings)

    faiss_dir = settings.faiss_dir
    index.save(faiss_dir)

    # Clear search cache since the index has changed
    conn = get_connection(db_path)
    conn.execute("DELETE FROM search_cache")
    conn.commit()
    conn.close()

    # Update module-level cache
    _search_index = index
    _search_index_db_path = db_path or settings.db_path


def _hash_query(query: str) -> str:
    """Hash a query string for cache lookup."""
    return hashlib.sha256(query.encode("utf-8")).hexdigest()


def _lookup_cache(query_hash: str, db_path: str | None = None) -> list[int] | None:
    """Check search_cache for a non-expired entry. Returns media ID list or None."""
    conn = get_connection(db_path)
    row = conn.execute(
        "SELECT result_ids, created_at FROM search_cache WHERE query_hash = ?",
        (query_hash,),
    ).fetchone()
    conn.close()

    if row is None:
        return None

    # Check TTL
    created_at = row["created_at"]
    try:
        created_dt = datetime.fromisoformat(created_at)
        age = (datetime.now(timezone.utc) - created_dt).total_seconds()
        if age > CACHE_TTL_SECONDS:
            return None
    except (ValueError, TypeError):
        return None

    try:
        result_ids = json.loads(row["result_ids"])
        if not result_ids:
            return None  # Don't serve empty cached results
        return result_ids
    except (json.JSONDecodeError, TypeError):
        return None


def _store_cache(query_hash: str, query_text: str, result_ids: list[int],
                 db_path: str | None = None) -> None:
    """Store search results in cache, replacing any existing entry."""
    if not result_ids:
        return  # Don't cache empty results
    conn = get_connection(db_path)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO search_cache (query_hash, query_text, result_ids, created_at) "
        "VALUES (?, ?, ?, ?)",
        (query_hash, query_text, json.dumps(result_ids), now),
    )
    conn.commit()
    conn.close()


def search_by_text(query: str, limit: int = 20, cursor: int = 0,
                   db_path: str | None = None) -> dict:
    """Search media by text query using CLIP embeddings + FAISS.

    Returns dict with 'results' (list[MediaItem]) and 'next_cursor' (str|None).
    """
    query_hash = _hash_query(query)

    # Check cache first
    cached_ids = _lookup_cache(query_hash, db_path)
    if cached_ids is not None:
        result_ids = cached_ids
    else:
        # Embed text and search
        pipeline = get_embedding_pipeline()
        query_vec = pipeline.embed_text([query])

        index = get_search_index(db_path)
        search_results = index.search(query_vec, k=200)

        result_ids = [r[0] for r in search_results]

        # Cache the result
        _store_cache(query_hash, query, result_ids, db_path)

    # ── Face cluster label matching (hybrid search) ──
    conn = get_connection(db_path)
    matched_clusters = conn.execute(
        "SELECT id FROM face_clusters WHERE label LIKE ?",
        (f"%{query}%",),
    ).fetchall()
    if matched_clusters:
        cluster_ids = [r["id"] for r in matched_clusters]
        placeholders = ",".join("?" * len(cluster_ids))
        face_rows = conn.execute(
            f"SELECT DISTINCT media_id FROM faces WHERE cluster_id IN ({placeholders})",
            cluster_ids,
        ).fetchall()
        # Prepend face-matched media to top of results
        face_ids = [r["media_id"] for r in face_rows]
        seen = set(result_ids)
        result_ids = face_ids + [mid for mid in result_ids if mid not in seen]
    conn.close()

    # Paginate
    total = len(result_ids)
    page_ids = result_ids[cursor:cursor + limit]

    # Query media table preserving relevance order
    media_items = []
    if page_ids:
        conn = get_connection(db_path)
        # Build ordered results
        placeholders = ",".join("?" * len(page_ids))
        rows = conn.execute(
            f"SELECT * FROM media WHERE id IN ({placeholders})",
            page_ids,
        ).fetchall()
        conn.close()

        # Map by id for ordering
        row_map = {r["id"]: r for r in rows}
        media_items = [
            MediaItem.from_row(row_map[mid])
            for mid in page_ids
            if mid in row_map
        ]

    next_cursor = str(cursor + limit) if cursor + limit < total else None

    return {
        "results": media_items,
        "next_cursor": next_cursor,
    }


def search_by_image(file_bytes: bytes, limit: int = 20,
                    db_path: str | None = None) -> list[MediaItem]:
    """Search media by image similarity using CLIP embeddings + FAISS.

    Writes uploaded bytes to a temp file, generates embedding, searches index.
    """
    # Write bytes to temp file
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        pipeline = get_embedding_pipeline()
        query_vec = pipeline.embed_images([tmp_path])

        if query_vec.shape[0] == 0:
            return []

        index = get_search_index(db_path)
        search_results = index.search(query_vec, k=limit)

        result_ids = [r[0] for r in search_results]
        if not result_ids:
            return []

        # Query media table preserving relevance order
        conn = get_connection(db_path)
        placeholders = ",".join("?" * len(result_ids))
        rows = conn.execute(
            f"SELECT * FROM media WHERE id IN ({placeholders})",
            result_ids,
        ).fetchall()
        conn.close()

        row_map = {r["id"]: r for r in rows}
        return [
            MediaItem.from_row(row_map[mid])
            for mid in result_ids
            if mid in row_map
        ]
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
