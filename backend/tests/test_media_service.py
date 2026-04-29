# backend/tests/test_media_service.py
from app.services.media_service import (
    get_media_by_id,
    get_media_random,
    get_media_on_this_day,
    delete_media,
)
from app.database import get_connection


def _seed_media(conn):
    conn.execute(
        """INSERT INTO media (path, filename, media_type, date_taken, date_added, checksum)
           VALUES ('/p/1.jpg', '1.jpg', 'image', '2025-04-29T12:00:00', '2026-01-01T00:00:00', 'aaa')"""
    )
    conn.execute(
        """INSERT INTO media (path, filename, media_type, date_taken, date_added, checksum)
           VALUES ('/p/2.jpg', '2.jpg', 'image', '2024-04-29T08:00:00', '2026-01-01T00:00:00', 'bbb')"""
    )
    conn.execute(
        """INSERT INTO media (path, filename, media_type, date_taken, date_added, checksum)
           VALUES ('/p/3.jpg', '3.jpg', 'image', '2025-05-01T10:00:00', '2026-01-01T00:00:00', 'ccc')"""
    )
    conn.commit()


def test_get_media_by_id_found(tmp_db_path):
    conn = get_connection(tmp_db_path)
    _seed_media(conn)
    conn.close()

    item = get_media_by_id(1, db_path=tmp_db_path)
    assert item is not None
    assert item.filename == "1.jpg"


def test_get_media_by_id_not_found(tmp_db_path):
    item = get_media_by_id(999, db_path=tmp_db_path)
    assert item is None


def test_get_media_random(tmp_db_path):
    conn = get_connection(tmp_db_path)
    _seed_media(conn)
    conn.close()

    results = get_media_random(2, exclude_ids=[], db_path=tmp_db_path)
    assert len(results) == 2
    ids = [r.id for r in results]
    assert len(set(ids)) == 2  # no duplicates


def test_get_media_random_respects_exclude(tmp_db_path):
    conn = get_connection(tmp_db_path)
    _seed_media(conn)
    conn.close()

    results = get_media_random(10, exclude_ids=[1, 2], db_path=tmp_db_path)
    ids = [r.id for r in results]
    assert 1 not in ids
    assert 2 not in ids


def test_get_media_on_this_day(tmp_db_path):
    conn = get_connection(tmp_db_path)
    _seed_media(conn)
    conn.close()

    results = get_media_on_this_day(month=4, day=29, db_path=tmp_db_path)
    # Should include both 2025-04-29 and 2024-04-29
    dates = [r.date_taken for r in results]
    assert "2025-04-29T12:00:00" in dates
    assert "2024-04-29T08:00:00" in dates
    assert len(results) == 2


def test_delete_media_removes_record(tmp_db_path):
    conn = get_connection(tmp_db_path)
    _seed_media(conn)
    conn.close()

    success = delete_media(1, db_path=tmp_db_path)
    assert success is True

    item = get_media_by_id(1, db_path=tmp_db_path)
    assert item is None


def test_delete_media_nonexistent(tmp_db_path):
    success = delete_media(999, db_path=tmp_db_path)
    assert success is False
