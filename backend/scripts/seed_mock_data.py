"""Seed mock data into SQLite for frontend development."""
import sqlite3
import os
import sys
import random
import hashlib

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

COLOR_THEMES = [
    # (name, r, g, b) — real color palettes for variety
    ("蓝天", 100, 160, 220),
    ("绿草", 120, 190, 130),
    ("日落", 240, 170, 100),
    ("樱花", 245, 200, 210),
    ("海洋", 80, 150, 200),
    ("森林", 80, 140, 80),
    ("沙漠", 220, 190, 140),
    ("雪山", 220, 230, 240),
    ("城市", 160, 160, 170),
    ("花园", 230, 180, 200),
    ("秋叶", 210, 150, 90),
    ("夜空", 30, 40, 80),
    ("日出", 250, 200, 120),
    ("湖水", 100, 180, 170),
    ("麦田", 220, 210, 120),
    ("紫藤", 180, 150, 210),
    ("红墙", 200, 100, 90),
    ("竹林", 100, 170, 100),
    ("海滩", 240, 220, 180),
    ("云雾", 200, 210, 220),
]

MEDIA_DIR = settings.media_root


def _gen_png(filename: str, out_dir: str, r: int, g: int, b: int) -> str:
    """Generate a simple PNG image with color blocks and pattern in out_dir."""
    from PIL import Image, ImageDraw

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, filename)
    w, h = 400, 300

    img = Image.new("RGB", (w, h), (r, g, b))
    draw = ImageDraw.Draw(img)

    # Add lighter/darker stripes for visual variety
    for i in range(0, h, 20):
        shade = random.randint(-30, 30)
        stripe_r = max(0, min(255, r + shade))
        stripe_g = max(0, min(255, g + shade))
        stripe_b = max(0, min(255, b + shade))
        draw.rectangle([0, i, w, i + 10], fill=(stripe_r, stripe_g, stripe_b))

    # Add a circle (simulating a focal point)
    cx = w // 2 + random.randint(-80, 80)
    cy = h // 2 + random.randint(-60, 60)
    radius = random.randint(30, 80)
    circle_color = (
        max(0, min(255, r + random.randint(-80, -30))),
        max(0, min(255, g + random.randint(-80, -30))),
        max(0, min(255, b + random.randint(-80, -30))),
    )
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        fill=circle_color,
    )

    # Add some small shapes for texture
    for _ in range(random.randint(3, 8)):
        sx = random.randint(10, w - 10)
        sy = random.randint(10, h - 10)
        size = random.randint(5, 20)
        draw.rectangle([sx, sy, sx + size, sy + size], fill=(
            max(0, min(255, r + random.randint(-60, 60))),
            max(0, min(255, g + random.randint(-60, 60))),
            max(0, min(255, b + random.randint(-60, 60))),
        ))

    img.save(path, "PNG")
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

    base_date = datetime(2023, 1, 1)
    media_ids = []

    for i in range(50):
        days_offset = random.randint(0, 900)
        dt = base_date + timedelta(days=days_offset)
        date_taken = dt.strftime("%Y-%m-%dT%H:%M:%S")
        date_added = (dt + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%dT%H:%M:%S")
        w, h = random.choice([(4000, 3000), (3000, 4000), (1920, 1080), (3024, 4032)])
        loc = random.choice(LOCATIONS)

        theme = random.choice(COLOR_THEMES)
        theme_name, r, g, b = theme

        thumb_filename = f"mock_{i:03d}.png"
        # Save to both thumbnails directory and media directory (for original)
        _gen_png(thumb_filename, THUMB_DIR, r, g, b)
        _gen_png(thumb_filename, MEDIA_DIR, r, g, b)

        checksum = hashlib.sha256(f"mock_{i}".encode()).hexdigest()
        dhash = hashlib.md5(f"dhash_{i}".encode()).hexdigest()[:16]
        file_size = os.path.getsize(os.path.join(MEDIA_DIR, thumb_filename))

        cursor = conn.execute(
            """INSERT INTO media (path, filename, media_type, width, height, file_size,
               date_taken, date_added, thumbnail_path, duration, is_blurry, blur_score,
               dhash, checksum)
               VALUES (?, ?, 'image', ?, ?, ?, ?, ?, ?, NULL, 0, NULL, ?, ?)""",
            (
                thumb_filename,
                f"mock_{i:03d}",
                w, h,
                file_size,
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

    conn.commit()
    final_count = conn.execute("SELECT COUNT(*) FROM media").fetchone()[0]
    print(f"Seeded {final_count} media records, {len(event_ids)} events, {len(face_cluster_ids)} face clusters.")
    conn.close()


if __name__ == "__main__":
    reset = "--reset" in sys.argv
    seed(reset=reset)
