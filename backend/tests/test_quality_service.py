# backend/tests/test_quality_service.py
import time
from app.database import get_connection
from app.services.quality_service import (
    run_blur_check,
    run_duplicate_check,
    get_blurry_media,
    get_duplicate_pairs,
)
from app.services.scan_service import JobTracker


def test_run_blur_check_job(tmp_db_path):
    """run_blur_check should create a job and complete it."""
    conn = get_connection(tmp_db_path)
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added) VALUES (?,?,?,?)",
        ("/p/1.jpg", "1.jpg", "image", "2026-01-01T00:00:00"),
    )
    conn.commit()
    conn.close()

    job_id = run_blur_check(db_path=tmp_db_path)

    tracker = JobTracker()
    # Poll until completed (max 5 seconds)
    for _ in range(50):
        job = tracker.get(job_id)
        if job is not None and job["status"] in ("completed", "failed"):
            break
        time.sleep(0.1)

    job = tracker.get(job_id)
    assert job is not None, "Job not found in tracker"
    assert job["status"] == "completed", f"Expected completed, got {job['status']}: {job.get('error')}"
    assert job["processed"] == 1
    assert job["total"] == 1
    assert "blurry_count" in job

    # Verify DB was updated
    conn = get_connection(tmp_db_path)
    rows = conn.execute("SELECT id, is_blurry, blur_score FROM media").fetchall()
    conn.close()
    assert len(rows) == 1
    assert rows[0]["blur_score"] is not None


def test_run_blur_check_no_images(tmp_db_path):
    """run_blur_check with no images should complete with zero total."""
    job_id = run_blur_check(db_path=tmp_db_path)

    tracker = JobTracker()
    for _ in range(50):
        job = tracker.get(job_id)
        if job is not None and job["status"] in ("completed", "failed"):
            break
        time.sleep(0.1)

    job = tracker.get(job_id)
    assert job is not None
    assert job["status"] == "completed"
    assert job["total"] == 0


def test_run_duplicate_check_job(tmp_db_path):
    """run_duplicate_check should find duplicate pairs."""
    conn = get_connection(tmp_db_path)
    # Insert two media with identical dhash
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added, dhash) VALUES (?,?,?,?,?)",
        ("/p/a.jpg", "a.jpg", "image", "2026-01-01T00:00:00", "abcd123400000000"),
    )
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added, dhash) VALUES (?,?,?,?,?)",
        ("/p/b.jpg", "b.jpg", "image", "2026-01-02T00:00:00", "abcd123400000000"),
    )
    conn.commit()
    conn.close()

    job_id = run_duplicate_check(db_path=tmp_db_path)

    tracker = JobTracker()
    for _ in range(50):
        job = tracker.get(job_id)
        if job is not None and job["status"] in ("completed", "failed"):
            break
        time.sleep(0.1)

    job = tracker.get(job_id)
    assert job is not None
    assert job["status"] == "completed"
    assert job["total"] == 1  # one pair
    assert len(job["pairs"]) == 1
    assert job["pairs"][0] == (1, 2)


def test_run_duplicate_check_no_dhash(tmp_db_path):
    """No dhash entries should produce zero pairs."""
    conn = get_connection(tmp_db_path)
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added) VALUES (?,?,?,?)",
        ("/p/a.jpg", "a.jpg", "image", "2026-01-01T00:00:00"),
    )
    conn.commit()
    conn.close()

    job_id = run_duplicate_check(db_path=tmp_db_path)

    tracker = JobTracker()
    for _ in range(50):
        job = tracker.get(job_id)
        if job is not None and job["status"] in ("completed", "failed"):
            break
        time.sleep(0.1)

    job = tracker.get(job_id)
    assert job is not None
    assert job["status"] == "completed"
    assert job["total"] == 0
    assert job["pairs"] == []


def test_get_blurry_media(tmp_db_path):
    """get_blurry_media should return only media flagged as blurry."""
    conn = get_connection(tmp_db_path)
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added, is_blurry, blur_score) VALUES (?,?,?,?,?,?)",
        ("/p/a.jpg", "a.jpg", "image", "2026-01-01T00:00:00", 1, 50.0),
    )
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added, is_blurry, blur_score) VALUES (?,?,?,?,?,?)",
        ("/p/b.jpg", "b.jpg", "image", "2026-01-01T00:00:00", 0, 500.0),
    )
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added, is_blurry, blur_score) VALUES (?,?,?,?,?,?)",
        ("/p/c.jpg", "c.jpg", "image", "2026-01-01T00:00:00", 1, 30.0),
    )
    conn.commit()
    conn.close()

    items = get_blurry_media(threshold=100.0, limit=50, db_path=tmp_db_path)
    assert len(items) == 2
    ids = [item.id for item in items]
    assert 1 in ids
    assert 3 in ids
    assert 2 not in ids


def test_get_duplicate_pairs(tmp_db_path):
    """get_duplicate_pairs should return MediaItem pairs for duplicates."""
    conn = get_connection(tmp_db_path)
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added, dhash) VALUES (?,?,?,?,?)",
        ("/p/a.jpg", "a.jpg", "image", "2026-01-01T00:00:00", "aaaa000000000000"),
    )
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added, dhash) VALUES (?,?,?,?,?)",
        ("/p/b.jpg", "b.jpg", "image", "2026-01-02T00:00:00", "aaaa000000000000"),
    )
    conn.commit()
    conn.close()

    pairs = get_duplicate_pairs(db_path=tmp_db_path)
    assert len(pairs) == 1
    m1, m2 = pairs[0]
    assert m1.filename == "a.jpg"
    assert m2.filename == "b.jpg"
    assert isinstance(m1.id, int)
    assert isinstance(m2.id, int)


def test_get_duplicate_pairs_empty(tmp_db_path):
    """No duplicates should return empty list."""
    pairs = get_duplicate_pairs(db_path=tmp_db_path)
    assert pairs == []
