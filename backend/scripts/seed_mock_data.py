"""Seed mock data into SQLite for frontend development."""
import sqlite3
import os
import sys
import random
import hashlib
import struct
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.database import SCHEMA, get_connection
from app.config import settings

THUMB_DIR = settings.thumb_dir
DATA_DIR = settings.data_root

LOCATIONS = [
    ("杭州西湖", "杭州"),
    ("北京故宫", "北京"),
    ("上海外滩", "上海"),
    ("成都熊猫基地", "成都"),
    ("三亚亚龙湾", "三亚"),
    ("西安兵马俑", "西安"),
    ("丽江古城", "丽江"),
    ("厦门鼓浪屿", "厦门"),
]


def _gen_svg_thumb(filename: str, r: int, g: int, b: int) -> str:
    os.makedirs(THUMB_DIR, exist_ok=True)
    path = os.path.join(THUMB_DIR, filename)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300">'
        f'<rect width="300" height="300" fill="rgb({r},{g},{b})"/>'
        f'<text x="150" y="155" text-anchor="middle" font-size="48" fill="white">📷</text>'
        f'</svg>'
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return filename


def seed(reset: bool = False):
    conn = get_connection()
    if reset:
        conn.executescript("""
            DELETE FROM event_media;
            DELETE FROM events;
            DELETE FROM faces;
            DELETE FROM face_clusters;
            DELETE FROM embeddings;
            DELETE FROM search_cache;
            DELETE FROM media;
        """)
        conn.commit()
        conn.executescript(SCHEMA)
        conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM media").fetchone()[0]
    if count > 0:
        print(f"Already {count} media records. Use --reset to clear first.")
        conn.close()
        return

    base_date = datetime(2024, 1, 1)
    media_ids = []

    for i in range(50):
        days_offset = random.randint(0, 900)
        dt = base_date + timedelta(days=days_offset)
        date_taken = dt.strftime("%Y-%m-%dT%H:%M:%S")
        date_added = (dt + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%dT%H:%M:%S")
        w, h = random.choice([(4000, 3000), (3000, 4000), (1920, 1080), (3024, 4032)])
        loc = random.choice(LOCATIONS)

        r, g, b = random.randint(180, 240), random.randint(160, 220), random.randint(170, 230)
        thumb_filename = f"mock_{i:03d}.svg"
        _gen_svg_thumb(thumb_filename, r, g, b)

        filename = f"IMG_{20230101 + i:04d}.jpg"
        checksum = hashlib.sha256(f"mock_{i}".encode()).hexdigest()
        dhash = hashlib.md5(f"dhash_{i}".encode()).hexdigest()[:16]

        cursor = conn.execute(
            """INSERT INTO media (path, filename, media_type, width, height, file_size,
               date_taken, date_added, thumbnail_path, duration, is_blurry, blur_score,
               dhash, checksum)
               VALUES (?, ?, 'image', ?, ?, ?, ?, ?, ?, NULL, 0, NULL, ?, ?)""",
            (
                f"C:/Photos/Mock/{filename}",
                filename,
                w, h,
                random.randint(2_000_000, 15_000_000),
                date_taken,
                date_added,
                thumb_filename,
                dhash,
                checksum,
            ),
        )
        media_ids.append(cursor.lastrowid)

    events_data = [
        ("2024年3月 · 杭州西湖", "2024-03-15", "2024-03-16", "杭州西湖"),
        ("2024年8月 · 三亚亚龙湾", "2024-08-10", "2024-08-14", "三亚亚龙湾"),
        ("2025年1月 · 北京故宫", "2025-01-20", "2025-01-20", "北京故宫"),
    ]
    event_ids = []
    for title, start, end, loc in events_data:
        cursor = conn.execute(
            "INSERT INTO events (title, start_date, end_date, cover_media_id, media_count, location) VALUES (?, ?, ?, ?, 0, ?)",
            (title, start, end, media_ids[len(event_ids) % len(media_ids)], loc),
        )
        event_ids.append(cursor.lastrowid)

    for ei, eid in enumerate(event_ids):
        start_idx = ei * 4
        for mi in media_ids[start_idx : start_idx + random.randint(4, 8)]:
            conn.execute(
                "INSERT INTO event_media (event_id, media_id, sort_order) VALUES (?, ?, ?)",
                (eid, mi, 0),
            )
        conn.execute("UPDATE events SET media_count = (SELECT COUNT(*) FROM event_media WHERE event_id = ?) WHERE id = ?", (eid, eid))

    face_cluster_ids = []
    for i in range(3):
        cursor = conn.execute(
            "INSERT INTO face_clusters (label, cover_face_id, photo_count) VALUES (?, NULL, 0)",
            (f"人物 {i + 1}",),
        )
        face_cluster_ids.append(cursor.lastrowid)

    for mi in media_ids[:5]:
        random_vector = struct.pack(f"{512}f", *[random.uniform(-1, 1) for _ in range(512)])
        conn.execute(
            "INSERT OR IGNORE INTO embeddings (media_id, vector, model_version, created_at) VALUES (?, ?, 'chinese-clip-vit-base', ?)",
            (mi, random_vector, datetime.now().strftime("%Y-%m-%dT%H:%M:%S")),
        )

    conn.commit()
    final_count = conn.execute("SELECT COUNT(*) FROM media").fetchone()[0]
    print(f"Seeded {final_count} media records, {len(event_ids)} events, {len(face_cluster_ids)} face clusters.")
    conn.close()


if __name__ == "__main__":
    reset = "--reset" in sys.argv
    seed(reset=reset)
