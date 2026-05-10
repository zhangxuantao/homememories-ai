# backend/app/services/media_service.py
import numpy as np
from app.database import get_connection
from app.models import MediaItem
from app.services.search_service import get_search_index


def get_media_by_id(media_id: int, db_path: str | None = None) -> MediaItem | None:
    conn = get_connection(db_path)
    row = conn.execute("SELECT * FROM media WHERE id = ?", (media_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return MediaItem.from_row(row)


def get_media_random(
    count: int = 4, exclude_ids: list[int] | None = None, db_path: str | None = None
) -> list[MediaItem]:
    conn = get_connection(db_path)
    exclude = exclude_ids or []
    if exclude:
        placeholders = ",".join("?" * len(exclude))
        rows = conn.execute(
            f"SELECT * FROM media WHERE id NOT IN ({placeholders}) ORDER BY RANDOM() LIMIT ?",
            (*exclude, count),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM media ORDER BY RANDOM() LIMIT ?", (count,)
        ).fetchall()
    conn.close()
    return [MediaItem.from_row(r) for r in rows]


def get_media_on_this_day(
    month: int, day: int, db_path: str | None = None
) -> list[MediaItem]:
    conn = get_connection(db_path)
    rows = conn.execute(
        """SELECT * FROM media
           WHERE date_taken IS NOT NULL
           AND CAST(strftime('%m', date_taken) AS INTEGER) = ?
           AND CAST(strftime('%d', date_taken) AS INTEGER) = ?
           ORDER BY date_taken DESC""",
        (month, day),
    ).fetchall()
    conn.close()
    return [MediaItem.from_row(r) for r in rows]


def get_similar_media(
    media_id: int, limit: int = 20, db_path: str | None = None
) -> list[MediaItem]:
    conn = get_connection(db_path)
    row = conn.execute(
        "SELECT vector FROM embeddings WHERE media_id = ?", (media_id,)
    ).fetchone()
    conn.close()

    if row is None:
        return []

    blob = row["vector"]
    query_vec = np.frombuffer(blob, dtype=np.float32).copy()

    index = get_search_index(db_path)
    if index.id_map is None:
        return []

    search_results = index.search(query_vec, k=limit + 1)

    similar_ids = [
        r[0] for r in search_results if r[0] != media_id
    ][:limit]

    if not similar_ids:
        return []

    conn = get_connection(db_path)
    placeholders = ",".join("?" * len(similar_ids))
    rows = conn.execute(
        f"SELECT * FROM media WHERE id IN ({placeholders})",
        similar_ids,
    ).fetchall()
    conn.close()

    row_map = {r["id"]: r for r in rows}
    return [
        MediaItem.from_row(row_map[mid])
        for mid in similar_ids
        if mid in row_map
    ]


def delete_media(media_id: int, db_path: str | None = None) -> bool:
    conn = get_connection(db_path)
    cursor = conn.execute("DELETE FROM media WHERE id = ?", (media_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted
