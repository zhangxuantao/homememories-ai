# backend/app/services/cluster_service.py
import os
import struct
import threading
import numpy as np

from app.database import get_connection
from app.services.scan_service import JobTracker


def run_clustering(
    db_path: str | None = None,
    threshold: float = 0.5,
    reset: bool = False,
) -> int:
    """Cluster face embeddings using FAISS cosine similarity.

    Returns the number of clusters created.
    """
    conn = get_connection(db_path)

    if reset:
        conn.execute("UPDATE faces SET cluster_id = NULL")
        conn.execute("DELETE FROM face_clusters")
        conn.commit()

    rows = conn.execute(
        "SELECT id, embedding FROM faces WHERE embedding IS NOT NULL"
    ).fetchall()

    if len(rows) < 2:
        conn.close()
        return 0

    # ── Load embeddings ──
    face_ids = []
    vectors = []
    for row in rows:
        blob = row["embedding"]
        if blob is None:
            continue
        try:
            vec = np.frombuffer(blob, dtype=np.float32).copy()
            if vec.shape[0] != 512:
                continue
        except Exception:
            continue
        face_ids.append(row["id"])
        vectors.append(vec)

    if len(face_ids) < 2:
        conn.close()
        return 0

    embeddings = np.stack(vectors, axis=0).astype(np.float32)

    # ── L2 normalize for cosine similarity ──
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    embeddings = embeddings / norms

    # ── FAISS index ──
    import faiss

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    # ── Range search: find all neighbors above threshold ──
    lims, D, I = index.range_search(embeddings, threshold)

    # ── Union-Find ──
    n = len(face_ids)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i in range(n):
        start = lims[i]
        end = lims[i + 1]
        for j_idx in range(start, end):
            j = I[j_idx]
            if i != j and D[j_idx] >= threshold:
                union(i, j)

    # ── Group by root ──
    groups: dict[int, list[int]] = {}
    for i in range(n):
        root = find(i)
        groups.setdefault(root, []).append(face_ids[i])

    # ── Assign clusters ──
    cluster_count = 0
    for face_id_list in groups.values():
        if len(face_id_list) < 1:
            continue

        cursor = conn.execute(
            "INSERT INTO face_clusters (label, cover_face_id, photo_count) VALUES (NULL, ?, ?)",
            (face_id_list[0], len(face_id_list)),
        )
        cluster_id = cursor.lastrowid

        for fid in face_id_list:
            conn.execute(
                "UPDATE faces SET cluster_id = ? WHERE id = ?",
                (cluster_id, fid),
            )

        cluster_count += 1

    conn.commit()
    conn.close()
    return cluster_count


def start_clustering_job(
    db_path: str | None = None,
    threshold: float = 0.5,
    reset: bool = False,
) -> str:
    """Start clustering as a background job with progress tracking."""
    tracker = JobTracker()
    job_id = tracker.create(total=0, processed=0, stage="face_clustering")

    def _run():
        tracker.update(job_id, status="running")
        try:
            count = run_clustering(db_path=db_path, threshold=threshold, reset=reset)
            tracker.update(
                job_id,
                status="completed",
                progress=100.0,
                processed=count,
                total=count,
            )
        except Exception as e:
            tracker.update(job_id, status="failed", error=str(e))

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return job_id
