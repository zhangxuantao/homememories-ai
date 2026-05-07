# backend/app/services/face_service.py
import os
import threading
import numpy as np

from app.database import get_connection
from app.config import settings
from app.services.scan_service import JobTracker


def start_face_detection(db_path: str | None = None) -> str:
    """Start a background job to detect faces in all images.

    Uses FaceDetector (InsightFace) to find faces in each image that
    hasn't already been processed. Stores bbox, embedding, and thumbnail
    in the faces table.

    Returns a job_id for tracking progress via JobTracker.
    """
    tracker = JobTracker()
    job_id = tracker.create(total=0, processed=0, stage="face_detection")

    def _run():
        tracker.update(job_id, status="running")
        try:
            from app.ai.face_detector import FaceDetector

            conn = get_connection(db_path)
            rows = conn.execute(
                "SELECT id, path FROM media "
                "WHERE media_type = 'image' "
                "AND id NOT IN (SELECT DISTINCT media_id FROM faces) "
                "ORDER BY id"
            ).fetchall()
            total = len(rows)
            conn.close()

            tracker.update(job_id, total=total, processed=0)

            if total == 0:
                tracker.update(job_id, status="completed", progress=100.0)
                return

            detector = FaceDetector.get_instance()
            thumb_dir = os.path.join(settings.data_root, "thumbs", "faces")

            conn = get_connection(db_path)
            processed = 0
            faces_found = 0

            for row in rows:
                media_id = row["id"]
                path = row["path"]

                faces = detector.detect(path, thumb_dir=thumb_dir)

                for face in faces:
                    # Convert numpy embedding to bytes for SQLite BLOB storage
                    embedding_bytes = face["embedding"].tobytes()
                    # Serialize bbox as comma-separated string
                    bbox_str = ",".join(str(v) for v in face["bbox"])
                    thumb_path = face.get("thumb_path")

                    conn.execute(
                        "INSERT INTO faces (media_id, bbox, embedding, thumbnail_path) "
                        "VALUES (?, ?, ?, ?)",
                        (media_id, bbox_str, embedding_bytes, thumb_path),
                    )
                    faces_found += 1

                processed += 1

                # Update progress periodically
                if processed % 5 == 0 or processed == total:
                    tracker.update(
                        job_id,
                        processed=processed,
                        progress=round(processed / total * 100, 1),
                        faces_found=faces_found,
                    )

            conn.commit()
            conn.close()

            # ── Run clustering after detection ──
            from app.services.cluster_service import run_clustering

            clusters = run_clustering(db_path=db_path)

            tracker.update(
                job_id,
                status="completed",
                progress=100.0,
                processed=processed,
                faces_found=faces_found,
                clusters=clusters,
            )
        except Exception as e:
            tracker.update(job_id, status="failed", error=str(e))

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return job_id
