# backend/app/services/upload_service.py
import os
import threading
from datetime import datetime, timezone

from app.database import get_connection
from app.config import settings
from app.scanner.scanner import file_checksum, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
from app.scanner.exif_extractor import extract_date_taken
from app.scanner.thumbnail import generate_thumbnail
from app.scanner.video_extractor import extract_video_info, generate_video_thumbnail


def handle_uploaded_files(file_paths: list[str], original_names: list[str] | None = None) -> list[dict]:
    """Insert uploaded files into media table and return created records."""
    conn = get_connection()
    date_added = datetime.now(timezone.utc).isoformat()
    results = []

    if original_names is None:
        original_names = [os.path.basename(p) for p in file_paths]

    for filepath, original_name in zip(file_paths, original_names):
        filename = original_name
        ext = os.path.splitext(filename)[1].lower()
        media_type = "image" if ext in IMAGE_EXTENSIONS else "video"
        csum = file_checksum(filepath)

        existing = conn.execute(
            "SELECT id FROM media WHERE checksum = ?", (csum,)
        ).fetchone()
        if existing:
            continue

        date_taken = None
        width = None
        height = None
        duration = None
        thumbnail_path = None

        if media_type == "image":
            from PIL import Image
            try:
                img = Image.open(filepath)
                width, height = img.size
            except Exception:
                pass
            date_taken = extract_date_taken(filepath)
            thumbnail_path = generate_thumbnail(filepath, settings.thumb_dir, settings.media_root)
        else:
            info = extract_video_info(filepath)
            width = info["width"]
            height = info["height"]
            duration = info["duration"]
            thumbnail_path = generate_video_thumbnail(filepath, settings.thumb_dir, settings.media_root)

        if date_taken is None:
            try:
                mtime = os.path.getmtime(filepath)
                date_taken = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
            except OSError:
                pass

        file_size = os.path.getsize(filepath)
        cursor = conn.execute(
            """INSERT INTO media
               (path, filename, media_type, width, height, file_size,
                date_taken, date_added, thumbnail_path, duration, checksum)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (filepath, filename, media_type, width, height, file_size,
             date_taken, date_added, thumbnail_path, duration, csum),
        )
        results.append({
            "id": cursor.lastrowid,
            "filename": filename,
            "media_type": media_type,
        })

    conn.commit()
    conn.close()

    if results:
        _start_async_processing([r["id"] for r in results])

    return results


def _start_async_processing(media_ids: list[int]) -> None:
    """Background thread: dHash + blur detection for uploaded media."""
    def _run():
        from app.ai.quality import detect_blur
        from app.services.search_service import _generate_all_embeddings

        conn = get_connection()
        for mid in media_ids:
            row = conn.execute("SELECT path FROM media WHERE id = ?", (mid,)).fetchone()
            if not row:
                continue
            try:
                from PIL import Image
                import imagehash
                img = Image.open(row["path"])
                dhash_val = str(imagehash.dhash(img))
                is_blurry, blur_score = detect_blur(row["path"])
                conn.execute(
                    "UPDATE media SET dhash = ?, is_blurry = ?, blur_score = ? WHERE id = ?",
                    (dhash_val, 1 if is_blurry else 0, blur_score, mid),
                )
            except Exception:
                pass
        conn.commit()
        conn.close()

        try:
            _generate_all_embeddings()
        except Exception:
            pass

    t = threading.Thread(target=_run, daemon=True)
    t.start()
