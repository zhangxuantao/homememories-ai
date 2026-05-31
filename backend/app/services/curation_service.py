# backend/app/services/curation_service.py
from app.database import get_connection


def compute_scores(month: str) -> list[dict]:
    """Compute curation scores for all photos in a given month."""
    conn = get_connection()

    media = conn.execute(
        "SELECT id, blur_score, is_blurry FROM media "
        "WHERE date_taken LIKE ? AND media_type = 'image'",
        (f"{month}%",),
    ).fetchall()

    if not media:
        conn.close()
        return []

    max_event_count = conn.execute(
        "SELECT MAX(cnt) FROM ("
        "  SELECT COUNT(*) AS cnt FROM event_media em "
        "  JOIN media m ON em.media_id = m.id "
        "  WHERE m.date_taken LIKE ? "
        "  GROUP BY em.event_id"
        ")",
        (f"{month}%",),
    ).fetchone()[0] or 1

    results = []
    for m in media:
        mid = m["id"]

        # Sharpness (0-1)
        blur = m["blur_score"] or 0
        if m["is_blurry"]:
            sharpness = 0.0
        else:
            sharpness = min(blur / 1000.0, 1.0)

        # Face bonus
        face_count = conn.execute(
            "SELECT COUNT(*) FROM faces WHERE media_id = ?", (mid,)
        ).fetchone()[0]
        has_face = 1.0 if face_count > 0 else 0.0

        # Event participation
        event_count = conn.execute(
            "SELECT COUNT(*) FROM event_media em "
            "JOIN media m2 ON em.media_id = m2.id "
            "WHERE em.event_id IN ("
            "  SELECT event_id FROM event_media WHERE media_id = ?"
            ")",
            (mid,),
        ).fetchone()[0]
        event_participation = min(event_count / max(max_event_count, 1), 1.0)

        score = sharpness * 0.4 + has_face * 0.3 + event_participation * 0.3
        results.append({"media_id": mid, "score": round(score, 4)})

    conn.close()
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:20]


def generate_curation(month: str) -> dict:
    """Generate curated collection for a month."""
    from datetime import datetime, timezone

    scores = compute_scores(month)
    if not scores:
        return {"month": month, "count": 0, "items": []}

    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()

    conn.execute("DELETE FROM curated_photos WHERE month = ?", (month,))

    for rank, item in enumerate(scores, 1):
        conn.execute(
            "INSERT OR REPLACE INTO curated_photos (media_id, month, score, rank, generated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (item["media_id"], month, item["score"], rank, now),
        )

    conn.commit()
    conn.close()
    return {"month": month, "count": len(scores), "generated_at": now}


def get_curation(month: str) -> dict:
    """Get curated photos for a month."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT cp.*, m.filename, m.thumbnail_path, m.date_taken, "
        "m.width, m.height, m.media_type "
        "FROM curated_photos cp "
        "JOIN media m ON cp.media_id = m.id "
        "WHERE cp.month = ? "
        "ORDER BY cp.rank",
        (month,),
    ).fetchall()
    conn.close()

    return {
        "month": month,
        "items": [
            {
                "id": r["media_id"],
                "score": r["score"],
                "rank": r["rank"],
                "filename": r["filename"],
                "thumbnail_path": r["thumbnail_path"],
                "date_taken": r["date_taken"],
                "width": r["width"],
                "height": r["height"],
                "media_type": r["media_type"],
            }
            for r in rows
        ],
    }
