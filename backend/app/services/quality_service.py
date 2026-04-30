# backend/app/services/quality_service.py
import os
import threading

from app.database import get_connection
from app.models import MediaItem
from app.config import settings
from app.ai.quality import detect_blur, find_duplicates
from app.services.scan_service import JobTracker


def run_blur_check(threshold: float = 100.0, db_path: str | None = None) -> str:
    """Start a background job to scan all images for blur.

    Updates is_blurry and blur_score columns in the media table.
    Returns a job_id for tracking progress via JobTracker.
    """
    tracker = JobTracker()
    job_id = tracker.create(total=0, processed=0, stage="blur_check")

    def _run():
        tracker.update(job_id, status="running")
        try:
            conn = get_connection(db_path)
            rows = conn.execute(
                "SELECT id, path FROM media WHERE media_type = 'image' ORDER BY id"
            ).fetchall()
            total = len(rows)
            conn.close()

            tracker.update(job_id, total=total, processed=0)

            if total == 0:
                tracker.update(job_id, status="completed", progress=100.0)
                return

            conn = get_connection(db_path)
            processed = 0
            blurry_count = 0
            for row in rows:
                media_id = row["id"]
                path = row["path"]
                is_blurry, score = detect_blur(path, threshold)
                conn.execute(
                    "UPDATE media SET is_blurry = ?, blur_score = ? WHERE id = ?",
                    (1 if is_blurry else 0, score, media_id),
                )
                processed += 1
                if is_blurry:
                    blurry_count += 1

                # Update progress periodically
                if processed % 10 == 0 or processed == total:
                    tracker.update(
                        job_id,
                        processed=processed,
                        progress=round(processed / total * 100, 1),
                        blurry_count=blurry_count,
                    )

            conn.commit()
            conn.close()

            tracker.update(
                job_id,
                status="completed",
                progress=100.0,
                processed=processed,
                blurry_count=blurry_count,
            )
        except Exception as e:
            tracker.update(job_id, status="failed", error=str(e))

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return job_id


def run_duplicate_check(db_path: str | None = None) -> str:
    """Start a background job to find duplicate media pairs by dhash comparison.

    Results are stored in the job's 'pairs' field.
    Returns a job_id for tracking progress via JobTracker.
    """
    tracker = JobTracker()
    job_id = tracker.create(total=0, pairs=[], stage="duplicate_check")

    def _run():
        tracker.update(job_id, status="running")
        try:
            pairs = find_duplicates(db_path)
            tracker.update(
                job_id,
                status="completed",
                progress=100.0,
                pairs=pairs,
                total=len(pairs),
            )
        except Exception as e:
            tracker.update(job_id, status="failed", error=str(e))

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return job_id


def get_blurry_media(
    threshold: float | None = None,
    limit: int = 50,
    db_path: str | None = None,
) -> list[MediaItem]:
    """Query media records flagged as blurry."""
    conn = get_connection(db_path)
    if threshold is not None:
        rows = conn.execute(
            "SELECT * FROM media WHERE is_blurry = 1 AND blur_score < ? "
            "ORDER BY blur_score ASC LIMIT ?",
            (threshold, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM media WHERE is_blurry = 1 "
            "ORDER BY blur_score ASC LIMIT ?",
            (limit,),
        ).fetchall()
    conn.close()
    return [MediaItem.from_row(r) for r in rows]


def get_duplicate_pairs(
    db_path: str | None = None,
) -> list[tuple[MediaItem, MediaItem]]:
    """Query duplicate media pairs from the database using dhash comparison.

    This calls find_duplicates and maps IDs back to MediaItem objects.
    """
    pairs = find_duplicates(db_path)
    if not pairs:
        return []

    # Collect all unique media IDs
    unique_ids = set()
    for a, b in pairs:
        unique_ids.add(a)
        unique_ids.add(b)

    # Fetch media items
    conn = get_connection(db_path)
    placeholders = ",".join("?" * len(unique_ids))
    rows = conn.execute(
        f"SELECT * FROM media WHERE id IN ({placeholders})",
        list(unique_ids),
    ).fetchall()
    conn.close()

    row_map = {r["id"]: MediaItem.from_row(r) for r in rows}

    result = []
    for a, b in pairs:
        item_a = row_map.get(a)
        item_b = row_map.get(b)
        if item_a is not None and item_b is not None:
            result.append((item_a, item_b))

    return result
