# backend/app/services/scan_service.py
import uuid
import os
import threading
from app.database import get_connection
from app.models import ScanResult, JobStatus, SystemStats
from app.scanner.scanner import scan_directory
from app.config import settings


class JobTracker:
    """Generic singleton job tracker used by scan, embeddings, face, and quality jobs."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._jobs = {}
        return cls._instance

    def create(self, **extra_fields) -> str:
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = {
            "status": "pending",
            "progress": 0.0,
            "error": None,
            **extra_fields,
        }
        return job_id

    def update(self, job_id: str, **kwargs):
        if job_id in self._jobs:
            self._jobs[job_id].update(kwargs)

    def get(self, job_id: str) -> dict | None:
        return self._jobs.get(job_id)


# Backward compatibility alias
ScanJobTracker = JobTracker


def start_scan_job(source_dir: str | None = None) -> str:
    tracker = JobTracker()
    job_id = tracker.create(total=0, new=0, skipped=0)

    def _run_scan():
        tracker.update(job_id, status="running")
        try:
            target_dir = source_dir or settings.media_root
            result = scan_directory(target_dir, settings.thumb_dir)
            tracker.update(
                job_id,
                status="completed",
                progress=100.0,
                total=result["total"],
                new=result["new"],
                skipped=result["skipped"],
            )
        except Exception as e:
            tracker.update(job_id, status="failed", error=str(e))

    thread = threading.Thread(target=_run_scan, daemon=True)
    thread.start()
    return job_id


def get_scan_status(job_id: str) -> ScanResult | None:
    tracker = JobTracker()
    job = tracker.get(job_id)
    if job is None:
        return None
    return ScanResult(job_id=job_id, **job)


def get_job_status(job_id: str) -> JobStatus | None:
    tracker = JobTracker()
    job = tracker.get(job_id)
    if job is None:
        return None
    return JobStatus(job_id=job_id, **job)


def get_system_stats(db_path: str | None = None) -> SystemStats:
    conn = get_connection(db_path)
    db_path_actual = db_path or os.path.join(settings.data_root, "metadata.db")

    media_count = conn.execute("SELECT COUNT(*) FROM media").fetchone()[0]
    image_count = conn.execute(
        "SELECT COUNT(*) FROM media WHERE media_type = 'image'"
    ).fetchone()[0]
    video_count = conn.execute(
        "SELECT COUNT(*) FROM media WHERE media_type = 'video'"
    ).fetchone()[0]
    last_scan = conn.execute(
        "SELECT date_added FROM media ORDER BY date_added DESC LIMIT 1"
    ).fetchone()

    db_size = os.path.getsize(db_path_actual) if os.path.exists(db_path_actual) else 0

    conn.close()
    return SystemStats(
        db_size_bytes=db_size,
        media_count=media_count,
        image_count=image_count,
        video_count=video_count,
        last_scan_time=last_scan["date_added"] if last_scan else None,
    )
