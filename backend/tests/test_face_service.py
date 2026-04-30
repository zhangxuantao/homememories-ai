# backend/tests/test_face_service.py
import sys
import time
import numpy as np
from unittest.mock import patch, MagicMock
from PIL import Image

from app.database import get_connection
from app.services.face_service import start_face_detection
from app.services.scan_service import JobTracker


def test_start_face_detection_job(tmp_path, monkeypatch, tmp_db_path):
    """start_face_detection should create a job, detect faces, and populate the faces table."""
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))

    # Create actual test image files
    img1_path = str(tmp_path / "img1.jpg")
    img2_path = str(tmp_path / "img2.jpg")
    Image.new("RGB", (640, 480), color=(255, 200, 200)).save(img1_path, "JPEG")
    Image.new("RGB", (640, 480), color=(200, 255, 200)).save(img2_path, "JPEG")

    # Insert test images
    conn = get_connection(tmp_db_path)
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_added) VALUES (?,?,?,?,?)",
        (1, img1_path, "img1.jpg", "image", "2026-01-01T00:00:00"),
    )
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_added) VALUES (?,?,?,?,?)",
        (2, img2_path, "img2.jpg", "image", "2026-01-02T00:00:00"),
    )
    conn.commit()
    conn.close()

    # Mock FaceDetector to return one face per image
    fake_bbox = [10.0, 20.0, 100.0, 120.0]
    fake_embedding = np.random.randn(512).astype(np.float32)

    mock_face = MagicMock()
    mock_face.bbox = fake_bbox
    mock_face.embedding = fake_embedding

    mock_is = MagicMock()
    mock_model = MagicMock()
    mock_model.get.return_value = [mock_face]
    mock_is.app.FaceAnalysis.return_value = mock_model

    with patch.dict(sys.modules, {"insightface": mock_is}):
        from app.ai.face_detector import FaceDetector
        FaceDetector._instance = None

        job_id = start_face_detection(db_path=tmp_db_path)

        # Poll until completed (must stay inside patch.dict for bg thread)
        tracker = JobTracker()
        for _ in range(50):
            job = tracker.get(job_id)
            if job is not None and job["status"] in ("completed", "failed"):
                break
            time.sleep(0.1)

    job = tracker.get(job_id)
    assert job is not None, "Job not found in tracker"
    assert job["status"] == "completed", f"Expected completed, got {job['status']}: {job.get('error')}"
    assert job["total"] == 2
    assert job["processed"] == 2
    assert job["faces_found"] == 2

    # Verify faces table was populated
    conn = get_connection(tmp_db_path)
    face_rows = conn.execute("SELECT id, media_id, bbox, thumbnail_path FROM faces").fetchall()
    conn.close()

    assert len(face_rows) == 2
    # Check bbox was stored as comma-separated string
    assert "10.0" in face_rows[0]["bbox"]
    assert "100.0" in face_rows[0]["bbox"]
    # Verify both media_ids are present
    media_ids = {r["media_id"] for r in face_rows}
    assert media_ids == {1, 2}


def test_start_face_detection_skips_existing(tmp_path, monkeypatch, tmp_db_path):
    """Media that already have face records should be skipped."""
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))

    # Create actual test image files
    img1_path = str(tmp_path / "img1.jpg")
    img2_path = str(tmp_path / "img2.jpg")
    Image.new("RGB", (640, 480), color=(255, 200, 200)).save(img1_path, "JPEG")
    Image.new("RGB", (640, 480), color=(200, 255, 200)).save(img2_path, "JPEG")

    conn = get_connection(tmp_db_path)
    # Insert two images
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_added) VALUES (?,?,?,?,?)",
        (1, img1_path, "img1.jpg", "image", "2026-01-01T00:00:00"),
    )
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_added) VALUES (?,?,?,?,?)",
        (2, img2_path, "img2.jpg", "image", "2026-01-02T00:00:00"),
    )
    # Insert existing face record for media_id=1
    conn.execute(
        "INSERT INTO faces (media_id, bbox, embedding, thumbnail_path) VALUES (?,?,?,?)",
        (1, "0,0,50,50", b"\x00" * 512 * 4, None),
    )
    conn.commit()
    conn.close()

    # Mock FaceDetector
    fake_bbox = [10.0, 20.0, 100.0, 120.0]
    fake_embedding = np.random.randn(512).astype(np.float32)

    mock_face = MagicMock()
    mock_face.bbox = fake_bbox
    mock_face.embedding = fake_embedding

    mock_is = MagicMock()
    mock_model = MagicMock()
    mock_model.get.return_value = [mock_face]
    mock_is.app.FaceAnalysis.return_value = mock_model

    with patch.dict(sys.modules, {"insightface": mock_is}):
        from app.ai.face_detector import FaceDetector
        FaceDetector._instance = None

        job_id = start_face_detection(db_path=tmp_db_path)

        # Poll until completed (must stay inside patch.dict for bg thread)
        tracker = JobTracker()
        for _ in range(50):
            job = tracker.get(job_id)
            if job is not None and job["status"] in ("completed", "failed"):
                break
            time.sleep(0.1)

    job = tracker.get(job_id)
    assert job is not None
    assert job["status"] == "completed", f"Expected completed, got {job['status']}"
    # Only media_id=2 should be processed (1 was skipped)
    assert job["total"] == 1
    assert job["processed"] == 1

    # Verify only two face rows total (1 pre-existing + 1 new)
    conn = get_connection(tmp_db_path)
    face_rows = conn.execute("SELECT media_id FROM faces ORDER BY media_id").fetchall()
    conn.close()
    assert len(face_rows) == 2
    media_ids = [r["media_id"] for r in face_rows]
    assert media_ids == [1, 2]
