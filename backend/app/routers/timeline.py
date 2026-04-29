# backend/app/routers/timeline.py
from fastapi import APIRouter, Query
from app.database import get_connection
from app.models import MediaItem

router = APIRouter(prefix="/api/timeline", tags=["timeline"])


@router.get("/years")
def get_years(db_path: str = None) -> list[int]:
    conn = get_connection(db_path)
    rows = conn.execute(
        """SELECT DISTINCT CAST(strftime('%Y', date_taken) AS INTEGER) AS year
           FROM media WHERE date_taken IS NOT NULL ORDER BY year DESC"""
    ).fetchall()
    conn.close()
    return [r["year"] for r in rows]


@router.get("/events")
def get_events(
    year: int = Query(...),
    month: int | None = Query(None),
    db_path: str = None,
) -> list[dict]:
    conn = get_connection(db_path)
    if month:
        rows = conn.execute(
            """SELECT * FROM events
               WHERE CAST(strftime('%Y', start_date) AS INTEGER) = ?
               AND CAST(strftime('%m', start_date) AS INTEGER) = ?
               ORDER BY start_date""",
            (year, month),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT * FROM events
               WHERE CAST(strftime('%Y', start_date) AS INTEGER) = ?
               ORDER BY start_date""",
            (year,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/event/{event_id}/media")
def get_event_media(
    event_id: int,
    cursor: str | None = Query(None),
    limit: int = Query(100, le=500),
    db_path: str = None,
) -> dict:
    conn = get_connection(db_path)
    if cursor:
        rows = conn.execute(
            """SELECT m.* FROM media m
               JOIN event_media em ON m.id = em.media_id
               WHERE em.event_id = ? AND m.date_taken > ?
               ORDER BY m.date_taken LIMIT ?""",
            (event_id, cursor, limit + 1),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT m.* FROM media m
               JOIN event_media em ON m.id = em.media_id
               WHERE em.event_id = ?
               ORDER BY m.date_taken LIMIT ?""",
            (event_id, limit + 1),
        ).fetchall()

    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]

    conn.close()
    items = [MediaItem.from_row(r).model_dump() for r in rows]
    next_cursor = items[-1]["date_taken"] if has_more and items else None
    return {"items": items, "next_cursor": next_cursor}
