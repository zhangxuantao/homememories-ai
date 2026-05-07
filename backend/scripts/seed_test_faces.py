"""Insert synthetic face embeddings with intentional clusters for testing.

Creates 3 groups of face embeddings (each group has similar vectors + noise)
so that clustering produces predictable results.
"""
import sys
import struct
import random
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.database import get_connection
from app.config import settings
from app.services.cluster_service import run_clustering

SEED = 42


def seed_test_faces(num_clusters: int = 4, faces_per_cluster: int = 8):
    """Create test face embeddings clustered around distinct centroids."""
    conn = get_connection()

    # Get media IDs to associate faces with
    media_rows = conn.execute(
        "SELECT id FROM media WHERE media_type = 'image' ORDER BY id LIMIT ?",
        (num_clusters * faces_per_cluster,),
    ).fetchall()

    if len(media_rows) < num_clusters * faces_per_cluster:
        print(f"Need {num_clusters * faces_per_cluster} media rows, only have {len(media_rows)}")
        conn.close()
        return

    # Generate cluster centroids (orthogonal-ish for clean separation)
    rng = np.random.default_rng(SEED)
    centroids = []
    for i in range(num_clusters):
        vec = rng.normal(0, 1, 512).astype(np.float32)
        vec = vec / np.linalg.norm(vec)
        centroids.append(vec)

    # Clear existing face data
    conn.execute("DELETE FROM faces")
    conn.execute("DELETE FROM face_clusters")
    conn.commit()

    # Generate faces around centroids with varying noise
    face_id = 0
    for cluster_idx in range(num_clusters):
        centroid = centroids[cluster_idx]
        for j in range(faces_per_cluster):
            media_id = media_rows[face_id]["id"]
            # Small noise for intra-cluster variation
            noise = rng.normal(0, 0.01, 512).astype(np.float32)
            vec = centroid + noise
            vec = vec / np.linalg.norm(vec)

            embedding_blob = vec.tobytes()
            bbox = f"{100+j*5},{100+j*3},{200+j*5},{200+j*3}"

            conn.execute(
                "INSERT INTO faces (media_id, bbox, embedding) VALUES (?, ?, ?)",
                (media_id, bbox, embedding_blob),
            )
            face_id += 1

    conn.commit()
    face_count = conn.execute("SELECT COUNT(*) FROM faces").fetchone()[0]
    conn.close()
    print(f"Inserted {face_count} test faces across {num_clusters} clusters")

    # Run clustering
    clusters = run_clustering(threshold=0.5)
    print(f"Clustering complete: {clusters} clusters created")


if __name__ == "__main__":
    seed_test_faces()
