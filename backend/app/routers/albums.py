from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone

from app.database import get_connection
from app.models import MediaItem

router = APIRouter(prefix="/api/albums", tags=["albums"])


class AlbumCreate(BaseModel):
    name: str


class AlbumAddMedia(BaseModel):
    media_ids: list[int]


class AlbumPatch(BaseModel):
    name: str | None = None
    cover_media_id: int | None = None


@router.get("")
def list_albums():
    conn = get_connection()
    rows = conn.execute(
        "SELECT a.*, m.thumbnail_path FROM albums a "
        "LEFT JOIN media m ON a.cover_media_id = m.id "
        "ORDER BY a.updated_at DESC"
    ).fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "cover_media_id": r["cover_media_id"],
            "cover_thumbnail": r["thumbnail_path"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }
        for r in rows
    ]


@router.post("")
def create_album(body: AlbumCreate):
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        "INSERT INTO albums (name, created_at, updated_at) VALUES (?, ?, ?)",
        (body.name, now, now),
    )
    conn.commit()
    album_id = cursor.lastrowid
    conn.close()
    return {"id": album_id, "name": body.name, "created_at": now}


@router.post("/{album_id}/media")
def add_media_to_album(album_id: int, body: AlbumAddMedia):
    conn = get_connection()
    album = conn.execute("SELECT id FROM albums WHERE id = ?", (album_id,)).fetchone()
    if not album:
        conn.close()
        raise HTTPException(status_code=404, detail="相册不存在")

    now = datetime.now(timezone.utc).isoformat()
    count = 0
    for mid in body.media_ids:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO album_media (album_id, media_id, sort_order) VALUES (?, ?, ?)",
                (album_id, mid, 9999),
            )
            count += 1
        except Exception:
            continue

    # Update cover if not set
    current_cover = conn.execute(
        "SELECT cover_media_id FROM albums WHERE id = ?", (album_id,)
    ).fetchone()
    if not current_cover["cover_media_id"] and body.media_ids:
        conn.execute(
            "UPDATE albums SET cover_media_id = ?, updated_at = ? WHERE id = ?",
            (body.media_ids[0], now, album_id),
        )

    conn.execute("UPDATE albums SET updated_at = ? WHERE id = ?", (now, album_id))
    conn.commit()
    conn.close()
    return {"added": count, "album_id": album_id}


@router.get("/{album_id}/media")
def get_album_media(album_id: int, limit: int = 100):
    conn = get_connection()
    rows = conn.execute(
        "SELECT m.* FROM media m "
        "JOIN album_media am ON m.id = am.media_id "
        "WHERE am.album_id = ? "
        "ORDER BY am.sort_order LIMIT ?",
        (album_id, limit),
    ).fetchall()
    conn.close()
    return {"items": [MediaItem.from_row(r).model_dump() for r in rows]}


@router.delete("/{album_id}/media")
def remove_media_from_album(album_id: int, media_ids: list[int]):
    conn = get_connection()
    for mid in media_ids:
        conn.execute(
            "DELETE FROM album_media WHERE album_id = ? AND media_id = ?",
            (album_id, mid),
        )
    conn.commit()
    conn.close()
    return {"deleted": len(media_ids)}


@router.get("/{album_id}")
def get_album(album_id: int):
    conn = get_connection()
    row = conn.execute(
        "SELECT a.*, m.thumbnail_path, "
        "(SELECT COUNT(*) FROM album_media WHERE album_id = a.id) AS media_count "
        "FROM albums a LEFT JOIN media m ON a.cover_media_id = m.id "
        "WHERE a.id = ?",
        (album_id,),
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="相册不存在")
    return {
        "id": row["id"],
        "name": row["name"],
        "cover_media_id": row["cover_media_id"],
        "cover_thumbnail": row["thumbnail_path"],
        "media_count": row["media_count"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@router.patch("/{album_id}")
def update_album(album_id: int, body: AlbumPatch):
    conn = get_connection()
    album = conn.execute("SELECT id FROM albums WHERE id = ?", (album_id,)).fetchone()
    if not album:
        conn.close()
        raise HTTPException(status_code=404, detail="相册不存在")

    now = datetime.now(timezone.utc).isoformat()
    if body.name is not None:
        conn.execute(
            "UPDATE albums SET name = ?, updated_at = ? WHERE id = ?",
            (body.name, now, album_id),
        )
    if body.cover_media_id is not None:
        conn.execute(
            "UPDATE albums SET cover_media_id = ?, updated_at = ? WHERE id = ?",
            (body.cover_media_id, now, album_id),
        )

    conn.commit()

    # Return updated album
    row = conn.execute(
        "SELECT a.*, m.thumbnail_path, "
        "(SELECT COUNT(*) FROM album_media WHERE album_id = a.id) AS media_count "
        "FROM albums a LEFT JOIN media m ON a.cover_media_id = m.id "
        "WHERE a.id = ?",
        (album_id,),
    ).fetchone()
    conn.close()
    return {
        "id": row["id"],
        "name": row["name"],
        "cover_media_id": row["cover_media_id"],
        "cover_thumbnail": row["thumbnail_path"],
        "media_count": row["media_count"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@router.delete("/{album_id}")
def delete_album(album_id: int):
    conn = get_connection()
    album = conn.execute("SELECT id FROM albums WHERE id = ?", (album_id,)).fetchone()
    if not album:
        conn.close()
        raise HTTPException(status_code=404, detail="相册不存在")

    conn.execute("DELETE FROM albums WHERE id = ?", (album_id,))
    conn.commit()
    conn.close()
    return {"deleted": album_id}
