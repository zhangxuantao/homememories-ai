# backend/tests/test_scanner.py
import os
from app.scanner.scanner import (
    file_checksum,
    scan_directory,
    is_image_file,
    is_video_file,
)


def test_file_checksum_deterministic(test_image):
    h1 = file_checksum(test_image)
    h2 = file_checksum(test_image)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex digest


def test_file_checksum_different_for_different_files(test_image, test_image_no_exif):
    h1 = file_checksum(test_image)
    h2 = file_checksum(test_image_no_exif)
    assert h1 != h2


def test_is_image_file():
    assert is_image_file("photo.jpg") is True
    assert is_image_file("photo.JPEG") is True
    assert is_image_file("photo.png") is True
    assert is_image_file("photo.gif") is False
    assert is_image_file("video.mp4") is False


def test_is_video_file():
    assert is_video_file("video.mp4") is True
    assert is_video_file("video.MOV") is True
    assert is_video_file("video.avi") is True
    assert is_video_file("photo.jpg") is False


def test_scan_directory_creates_media_records(tmp_path, tmp_db_path):
    from PIL import Image
    from PIL.ExifTags import Base
    from app.database import get_connection

    # Create test images in a temp media dir
    media_dir = tmp_path / "photos"
    media_dir.mkdir()
    img = Image.new("RGB", (200, 100), color=(100, 200, 100))
    exif = img.getexif()
    exif[Base.DateTimeOriginal] = "2025:06:20 10:00:00"
    img.save(str(media_dir / "summer.jpg"), "JPEG", exif=exif.tobytes())
    Image.new("RGB", (400, 300), color=(50, 50, 200)).save(
        str(media_dir / "winter.jpg"), "JPEG"
    )

    thumb_dir = str(tmp_path / "thumbs")

    result = scan_directory(str(media_dir), thumb_dir, db_path=tmp_db_path)

    assert result["total"] >= 2
    assert result["new"] >= 2
    assert result["skipped"] == 0

    conn = get_connection(tmp_db_path)
    rows = conn.execute("SELECT * FROM media ORDER BY filename").fetchall()
    assert len(rows) >= 2
    assert rows[0]["filename"] == "summer.jpg"
    assert rows[0]["date_taken"] == "2025-06-20T10:00:00"
    assert rows[0]["width"] == 200
    assert rows[0]["height"] == 100
    assert rows[0]["thumbnail_path"] is not None
    conn.close()


def test_scan_directory_skips_existing(tmp_path, tmp_db_path):
    from PIL import Image
    from app.database import get_connection

    media_dir = tmp_path / "photos"
    media_dir.mkdir()
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    img.save(str(media_dir / "single.jpg"), "JPEG")

    thumb_dir = str(tmp_path / "thumbs")

    # First scan
    r1 = scan_directory(str(media_dir), thumb_dir, db_path=tmp_db_path)
    assert r1["new"] == 1

    # Second scan — should skip
    r2 = scan_directory(str(media_dir), thumb_dir, db_path=tmp_db_path)
    assert r2["new"] == 0
    assert r2["skipped"] == 1
