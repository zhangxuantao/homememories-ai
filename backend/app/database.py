# backend/app/database.py
import sqlite3
import os
from app.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS media (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    filename TEXT NOT NULL,
    media_type TEXT NOT NULL,
    width INTEGER,
    height INTEGER,
    file_size INTEGER,
    date_taken TEXT,
    date_added TEXT NOT NULL,
    thumbnail_path TEXT,
    duration REAL,
    is_blurry BOOLEAN DEFAULT 0,
    blur_score REAL,
    dhash TEXT,
    checksum TEXT,
    embedding_id INTEGER
);

CREATE TABLE IF NOT EXISTS embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id INTEGER UNIQUE,
    vector BLOB NOT NULL,
    model_version TEXT,
    created_at TEXT,
    FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS faces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id INTEGER,
    cluster_id INTEGER,
    bbox TEXT,
    embedding BLOB,
    thumbnail_path TEXT,
    FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE,
    FOREIGN KEY (cluster_id) REFERENCES face_clusters(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS face_clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT,
    cover_face_id INTEGER,
    photo_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    start_date TEXT,
    end_date TEXT,
    cover_media_id INTEGER,
    media_count INTEGER DEFAULT 0,
    location TEXT,
    FOREIGN KEY (cover_media_id) REFERENCES media(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS event_media (
    event_id INTEGER,
    media_id INTEGER,
    sort_order INTEGER,
    PRIMARY KEY (event_id, media_id),
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS search_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_hash TEXT UNIQUE,
    query_text TEXT,
    result_ids TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS albums (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    cover_media_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (cover_media_id) REFERENCES media(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS album_media (
    album_id INTEGER,
    media_id INTEGER,
    sort_order INTEGER,
    PRIMARY KEY (album_id, media_id),
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE,
    FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id INTEGER NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_album_media_album ON album_media(album_id);

CREATE INDEX IF NOT EXISTS idx_media_date ON media(date_taken);
CREATE INDEX IF NOT EXISTS idx_media_type ON media(media_type);
CREATE INDEX IF NOT EXISTS idx_media_checksum ON media(checksum);
CREATE INDEX IF NOT EXISTS idx_media_dhash ON media(dhash);
CREATE INDEX IF NOT EXISTS idx_faces_cluster ON faces(cluster_id);
CREATE INDEX IF NOT EXISTS idx_faces_media ON faces(media_id);
CREATE INDEX IF NOT EXISTS idx_event_media_event ON event_media(event_id);
CREATE INDEX IF NOT EXISTS idx_favorites_created ON favorites(created_at DESC);
"""


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    path = db_path or os.path.join(settings.data_root, "metadata.db")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: str | None = None) -> None:
    conn = get_connection(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
