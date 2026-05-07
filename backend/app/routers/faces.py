# backend/app/routers/faces.py
import os
from fastapi import APIRouter, Query, HTTPException
from app.database import get_connection

router = APIRouter(prefix="/api/faces", tags=["faces"])


@router.get("/clusters")
def get_clusters():
    conn = get_connection()
    rows = conn.execute(
        """SELECT fc.id, fc.label, fc.cover_face_id, fc.photo_count,
                  f.thumbnail_path as cover_thumbnail
           FROM face_clusters fc
           LEFT JOIN faces f ON f.id = fc.cover_face_id
           ORDER BY fc.photo_count DESC"""
    ).fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "label": r["label"],
            "cover_face_id": r["cover_face_id"],
            "photo_count": r["photo_count"],
            "cover_thumbnail": os.path.basename(r["cover_thumbnail"]) if r["cover_thumbnail"] else None,
        }
        for r in rows
    ]


@router.get("/cluster/{cluster_id}/media")
def get_cluster_media(
    cluster_id: int,
    cursor: str | None = Query(None),
    limit: int = Query(100, le=500),
):
    conn = get_connection()
    if cursor:
        rows = conn.execute(
            """SELECT m.* FROM media m
               JOIN faces f ON f.media_id = m.id
               WHERE f.cluster_id = ?
                 AND m.date_taken < ?
               GROUP BY m.id
               ORDER BY m.date_taken DESC
               LIMIT ?""",
            (cluster_id, cursor, limit + 1),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT m.* FROM media m
               JOIN faces f ON f.media_id = m.id
               WHERE f.cluster_id = ?
               GROUP BY m.id
               ORDER BY m.date_taken DESC
               LIMIT ?""",
            (cluster_id, limit + 1),
        ).fetchall()

    conn.close()

    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]

    next_cursor = rows[-1]["date_taken"] if has_more and rows else None

    items = []
    for r in rows:
        items.append({
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
        })

    return {"items": items, "next_cursor": next_cursor}


@router.patch("/cluster/{cluster_id}")
def update_cluster_label(cluster_id: int, label: str = Query(..., min_length=1, max_length=50)):
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM face_clusters WHERE id = ?", (cluster_id,)
    ).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Cluster not found")
    conn.execute(
        "UPDATE face_clusters SET label = ? WHERE id = ?",
        (label, cluster_id),
    )
    conn.commit()
    conn.close()
    return {"id": cluster_id, "label": label}
