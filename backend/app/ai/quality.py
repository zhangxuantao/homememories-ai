# backend/app/ai/quality.py
import cv2
import numpy as np
from app.database import get_connection


def detect_blur(image_path: str, threshold: float = 100.0) -> tuple[bool, float]:
    """Laplacian variance blur detection. Returns (is_blurry, blur_score)."""
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return False, 0.0
        variance = cv2.Laplacian(img, cv2.CV_64F).var()
        return variance < threshold, float(variance)
    except Exception:
        return False, 0.0


def hamming_distance(hash1: str, hash2: str) -> int:
    """Compute Hamming distance between two hex dhash strings."""
    if not hash1 or not hash2:
        return 64
    return (int(hash1, 16) ^ int(hash2, 16)).bit_count()


def find_duplicates(db_path: str | None = None, hamming_threshold: int = 8) -> list[tuple[int, int]]:
    """Find duplicate media pairs by comparing dhash Hamming distances."""
    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT id, dhash FROM media WHERE dhash IS NOT NULL AND dhash != '' ORDER BY id"
    ).fetchall()
    conn.close()

    pairs = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            dist = hamming_distance(rows[i]["dhash"], rows[j]["dhash"])
            if dist <= hamming_threshold:
                pairs.append((rows[i]["id"], rows[j]["id"]))
    return pairs
