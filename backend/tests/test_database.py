# backend/tests/test_database.py
import sqlite3
import os
from app.database import get_connection, init_db, SCHEMA


def test_init_db_creates_tables(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()

    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    table_names = [r[0] for r in tables]

    assert "media" in table_names
    assert "embeddings" in table_names
    assert "faces" in table_names
    assert "face_clusters" in table_names
    assert "events" in table_names
    assert "event_media" in table_names
    assert "search_cache" in table_names
    conn.close()


def test_init_db_creates_indexes(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()

    indexes = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
    ).fetchall()
    index_names = [r[0] for r in indexes]

    assert "idx_media_date" in index_names
    assert "idx_media_type" in index_names
    assert "idx_media_checksum" in index_names
    assert "idx_faces_cluster" in index_names
    assert "idx_faces_media" in index_names
    conn.close()


def test_media_table_constraints(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)

    # path must be unique
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added) VALUES (?, ?, ?, ?)",
        ("/test/photo.jpg", "photo.jpg", "image", "2026-04-29T00:00:00"),
    )
    conn.commit()
    try:
        conn.execute(
            "INSERT INTO media (path, filename, media_type, date_added) VALUES (?, ?, ?, ?)",
            ("/test/photo.jpg", "photo.jpg", "image", "2026-04-29T00:00:00"),
        )
        conn.commit()
        assert False, "Should have raised IntegrityError"
    except sqlite3.IntegrityError:
        pass
    conn.close()
