# backend/tests/test_quality.py
import cv2
import numpy as np
from PIL import Image
from app.ai.quality import detect_blur, hamming_distance, find_duplicates
from app.database import get_connection


def test_detect_blur_sharp_image(tmp_path):
    """Synthetic sharp image should NOT be flagged as blurry."""
    # Use 800x600 and many sharp edges for high Laplacian variance
    arr = np.random.randint(0, 256, (600, 800, 3), dtype=np.uint8)
    # Add a sharp checkerboard pattern
    for i in range(0, 600, 20):
        for j in range(0, 800, 20):
            color = [0, 0, 0] if (i // 20 + j // 20) % 2 == 0 else [255, 255, 255]
            arr[i:i + 20, j:j + 20] = color
    img = Image.fromarray(arr)
    img_path = str(tmp_path / "sharp.png")
    img.save(img_path, "PNG")

    is_blurry, score = detect_blur(img_path)
    assert is_blurry == False, f"Expected sharp image, got blurry with score={score}"
    assert score > 100.0, f"Expected score > 100, got {score}"


def test_detect_blur_blurry_image(tmp_path):
    """Gaussian blurred image should be flagged as blurry."""
    # Create a checkerboard and heavily blur it
    arr = np.random.randint(0, 256, (600, 800, 3), dtype=np.uint8)
    for i in range(0, 600, 20):
        for j in range(0, 800, 20):
            color = [0, 0, 0] if (i // 20 + j // 20) % 2 == 0 else [255, 255, 255]
            arr[i:i + 20, j:j + 20] = color

    # Apply heavy Gaussian blur
    blurred = cv2.GaussianBlur(arr, (51, 51), 50)
    img = Image.fromarray(blurred)
    img_path = str(tmp_path / "blurry.png")
    img.save(img_path, "PNG")

    is_blurry, score = detect_blur(img_path)
    assert is_blurry == True, f"Expected blurry image, got sharp with score={score}"
    assert score < 100.0, f"Expected score < 100, got {score}"


def test_detect_blur_nonexistent_file():
    """Reading a nonexistent file should return (False, 0.0)."""
    is_blurry, score = detect_blur("/nonexistent/path/image.jpg")
    assert is_blurry is False
    assert score == 0.0


def test_hamming_distance_identical():
    """Identical hashes should have Hamming distance 0."""
    assert hamming_distance("abc123", "abc123") == 0


def test_hamming_distance_different():
    """Different hashes should return non-zero Hamming distance."""
    dist = hamming_distance("0000000000000000", "000000000000000F")
    assert dist > 0


def test_hamming_distance_empty():
    """Empty hashes should return 64 (max distance)."""
    assert hamming_distance("", "abc") == 64
    assert hamming_distance("abc", "") == 64
    assert hamming_distance("", "") == 64


def test_find_duplicates_with_similar_dhash(tmp_db_path):
    """Insert media with similar dhash values — pair should be detected."""
    conn = get_connection(tmp_db_path)
    # Same dhash → Hamming distance 0
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added, dhash) VALUES (?,?,?,?,?)",
        ("/a.jpg", "a.jpg", "image", "2026-01-01T00:00:00", "abc1230000000000"),
    )
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added, dhash) VALUES (?,?,?,?,?)",
        ("/b.jpg", "b.jpg", "image", "2026-01-01T00:00:00", "abc1230000000000"),
    )
    conn.commit()
    conn.close()

    pairs = find_duplicates(db_path=tmp_db_path)
    assert len(pairs) == 1
    assert pairs[0] == (1, 2)


def test_find_duplicates_no_dhash(tmp_db_path):
    """Media without dhash should not produce any duplicate pairs."""
    conn = get_connection(tmp_db_path)
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added) VALUES (?,?,?,?)",
        ("/a.jpg", "a.jpg", "image", "2026-01-01T00:00:00"),
    )
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added) VALUES (?,?,?,?)",
        ("/b.jpg", "b.jpg", "image", "2026-01-01T00:00:00"),
    )
    conn.commit()
    conn.close()

    pairs = find_duplicates(db_path=tmp_db_path)
    assert pairs == []


def test_find_duplicates_dissimilar_dhash(tmp_db_path):
    """Very different dhash values should not be flagged as duplicates."""
    conn = get_connection(tmp_db_path)
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added, dhash) VALUES (?,?,?,?,?)",
        ("/a.jpg", "a.jpg", "image", "2026-01-01T00:00:00", "1111111111111111"),
    )
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added, dhash) VALUES (?,?,?,?,?)",
        ("/b.jpg", "b.jpg", "image", "2026-01-01T00:00:00", "AAAAAAAAAAAAAAAA"),
    )
    conn.commit()
    conn.close()

    pairs = find_duplicates(db_path=tmp_db_path)
    assert pairs == []
