# backend/app/scanner/scanner.py
import os
import hashlib
from datetime import datetime, timezone
from app.database import get_connection
from app.scanner.exif_extractor import extract_date_taken
from app.scanner.thumbnail import generate_thumbnail

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}


def is_image_file(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in IMAGE_EXTENSIONS


def is_video_file(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in VIDEO_EXTENSIONS


def file_checksum(filepath: str) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def scan_directory(
    media_root: str, thumb_dir: str, db_path: str | None = None
) -> dict:
    conn = get_connection(db_path)
    date_added = datetime.now(timezone.utc).isoformat()

    total = 0
    new = 0
    skipped = 0

    for dirpath, _, filenames in os.walk(media_root):
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in IMAGE_EXTENSIONS and ext not in VIDEO_EXTENSIONS:
                continue

            total += 1
            filepath = os.path.join(dirpath, filename)

            # Check if already scanned by checksum
            csum = file_checksum(filepath)
            existing = conn.execute(
                "SELECT id FROM media WHERE checksum = ?", (csum,)
            ).fetchone()
            if existing:
                skipped += 1
                continue

            media_type = "image" if ext in IMAGE_EXTENSIONS else "video"
            date_taken = extract_date_taken(filepath) if media_type == "image" else None
            file_size = os.path.getsize(filepath)

            width = None
            height = None
            thumbnail_path = None

            if media_type == "image":
                from PIL import Image

                try:
                    img = Image.open(filepath)
                    width, height = img.size
                except Exception:
                    pass

                thumbnail_path = generate_thumbnail(filepath, thumb_dir, media_root)

            conn.execute(
                """INSERT INTO media
                   (path, filename, media_type, width, height, file_size,
                    date_taken, date_added, thumbnail_path, checksum)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    filepath, filename, media_type, width, height, file_size,
                    date_taken, date_added, thumbnail_path, csum,
                ),
            )
            new += 1

    conn.commit()
    conn.close()
    return {"total": total, "new": new, "skipped": skipped}
