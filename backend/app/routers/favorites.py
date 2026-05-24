from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timezone

from app.database import get_connection

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.post("/{media_id}")
def toggle_favorite(media_id: int):
    conn = get_connection()
    media = conn.execute("SELECT id FROM media WHERE id = ?", (media_id,)).fetchone()
    if not media:
        conn.close()
        raise HTTPException(status_code=404, detail="Media not found")

    existing = conn.execute(
        "SELECT id FROM favorites WHERE media_id = ?", (media_id,)
    ).fetchone()

    if existing:
        conn.execute("DELETE FROM favorites WHERE id = ?", (existing["id"],))
        conn.commit()
        conn.close()
        return {"favorited": False}
    else:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO favorites (media_id, created_at) VALUES (?, ?)",
            (media_id, now),
        )
        conn.commit()
        conn.close()
        return {"favorited": True}


@router.get("")
def list_favorites(limit: int = 50, offset: int = 0):
    conn = get_connection()
    rows = conn.execute(
        """SELECT m.*, f.created_at as fav_created_at
           FROM favorites f
           JOIN media m ON f.media_id = m.id
           ORDER BY f.created_at DESC
           LIMIT ? OFFSET ?""",
        (limit, offset),
    ).fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "path": r["path"],
            "filename": r["filename"],
            "media_type": r["media_type"],
            "width": r["width"],
            "height": r["height"],
            "file_size": r["file_size"],
            "date_taken": r["date_taken"],
            "date_added": r["date_added"],
            "thumbnail_path": r["thumbnail_path"],
            "duration": r["duration"],
            "is_blurry": bool(r["is_blurry"]),
            "fav_created_at": r["fav_created_at"],
        }
        for r in rows
    ]


@router.get("/recent")
def recent_favorites(limit: int = 6):
    return list_favorites(limit=limit, offset=0)


@router.get("/check")
def check_favorites(ids: str = Query("")):
    if not ids:
        return {}
    try:
        id_list = [int(x.strip()) for x in ids.split(",") if x.strip()]
    except ValueError:
        return {}
    if not id_list:
        return {}

    conn = get_connection()
    placeholders = ",".join("?" * len(id_list))
    rows = conn.execute(
        f"SELECT media_id FROM favorites WHERE media_id IN ({placeholders})",
        id_list,
    ).fetchall()
    conn.close()

    fav_set = {r["media_id"] for r in rows}
    return {str(mid): mid in fav_set for mid in id_list}
