# backend/tests/test_exif_extractor.py
from app.scanner.exif_extractor import extract_date_taken


def test_extract_date_taken_from_exif(test_image):
    result = extract_date_taken(test_image)
    assert result == "2025-05-15T14:30:00"


def test_extract_date_taken_no_exif(test_image_no_exif):
    result = extract_date_taken(test_image_no_exif)
    assert result is None


def test_extract_date_taken_nonexistent_file():
    result = extract_date_taken("/nonexistent/file.jpg")
    assert result is None


def test_extract_date_taken_video_file(tmp_path):
    """Video files return None (no EXIF date support yet)."""
    video_path = tmp_path / "test.mp4"
    video_path.write_bytes(b"\x00\x00\x00\x18ftypmp42")
    result = extract_date_taken(str(video_path))
    assert result is None
