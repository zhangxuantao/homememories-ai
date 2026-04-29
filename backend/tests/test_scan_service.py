# backend/tests/test_scan_service.py
from app.services.scan_service import (
    ScanJobTracker,
    start_scan_job,
    get_scan_status,
    get_system_stats,
)


class TestScanJobTracker:
    def test_create_job(self):
        tracker = ScanJobTracker()
        job_id = tracker.create()
        assert job_id is not None
        assert len(job_id) == 36  # UUID format

    def test_job_starts_pending(self):
        tracker = ScanJobTracker()
        job_id = tracker.create()
        status = tracker.get(job_id)
        assert status["status"] == "pending"
        assert status["progress"] == 0.0

    def test_update_job(self):
        tracker = ScanJobTracker()
        job_id = tracker.create()
        tracker.update(job_id, status="running", progress=50.0)
        status = tracker.get(job_id)
        assert status["status"] == "running"
        assert status["progress"] == 50.0

    def test_get_nonexistent_job(self):
        tracker = ScanJobTracker()
        assert tracker.get("nonexistent") is None


def test_get_system_stats_empty(tmp_db_path):
    stats = get_system_stats(db_path=tmp_db_path)
    assert stats.media_count == 0
    assert stats.image_count == 0
    assert stats.video_count == 0
    assert stats.last_scan_time is None


def test_get_system_stats_with_data(tmp_db_path):
    from app.database import get_connection

    conn = get_connection(tmp_db_path)
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added) VALUES (?,?,?,?)",
        ("/a.jpg", "a.jpg", "image", "2026-01-01T00:00:00"),
    )
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added) VALUES (?,?,?,?)",
        ("/b.mp4", "b.mp4", "video", "2026-01-02T00:00:00"),
    )
    conn.commit()
    conn.close()

    stats = get_system_stats(db_path=tmp_db_path)
    assert stats.media_count == 2
    assert stats.image_count == 1
    assert stats.video_count == 1
    assert stats.last_scan_time == "2026-01-02T00:00:00"
