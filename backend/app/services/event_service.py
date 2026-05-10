# backend/app/services/event_service.py
import threading
from datetime import datetime, timedelta, timezone

from app.database import get_connection
from app.services.scan_service import JobTracker

# Photos within this many hours of the previous photo belong to the same event
GAP_HOURS = 3
# Minimum photos required to form an event
MIN_PHOTOS = 3


def _parse_dt(iso_string: str | None) -> datetime | None:
    if iso_string is None:
        return None
    try:
        return datetime.fromisoformat(iso_string)
    except (ValueError, TypeError):
        return None


def start_event_generation(db_path: str | None = None) -> str:
    tracker = JobTracker()
    job_id = tracker.create(total=0, processed=0, stage="event_generation")

    def _run():
        tracker.update(job_id, status="running")
        try:
            events_created = _generate_events(db_path)
            tracker.update(
                job_id,
                status="completed",
                progress=100.0,
                total=events_created,
                processed=events_created,
            )
        except Exception as e:
            tracker.update(job_id, status="failed", error=str(e))

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return job_id


def _generate_events(db_path: str | None = None) -> int:
    conn = get_connection(db_path)

    rows = conn.execute(
        "SELECT id, date_taken FROM media "
        "WHERE date_taken IS NOT NULL "
        "ORDER BY date_taken"
    ).fetchall()

    if len(rows) < MIN_PHOTOS:
        conn.close()
        return 0

    # Cluster by time proximity
    clusters: list[list[tuple[int, datetime]]] = []
    current_cluster: list[tuple[int, datetime]] = []

    gap = timedelta(hours=GAP_HOURS)

    for r in rows:
        dt = _parse_dt(r["date_taken"])
        if dt is None:
            continue

        if not current_cluster:
            current_cluster.append((r["id"], dt))
        else:
            prev_dt = current_cluster[-1][1]
            if dt - prev_dt <= gap:
                current_cluster.append((r["id"], dt))
            else:
                if len(current_cluster) >= MIN_PHOTOS:
                    clusters.append(current_cluster)
                current_cluster = [(r["id"], dt)]

    # Don't forget the last cluster
    if len(current_cluster) >= MIN_PHOTOS:
        clusters.append(current_cluster)

    if not clusters:
        conn.close()
        return 0

    # Clear existing events and event_media
    conn.execute("DELETE FROM event_media")
    conn.execute("DELETE FROM events")

    for cluster in clusters:
        start_dt = cluster[0][1]
        end_dt = cluster[-1][1]
        media_count = len(cluster)

        # Title: "YYYY年M月D日" (single-day) or "YYYY年M月D日-D日" (multi-day)
        if start_dt.date() == end_dt.date():
            title = f"{start_dt.year}年{start_dt.month}月{start_dt.day}日"
        else:
            title = f"{start_dt.year}年{start_dt.month}月{start_dt.day}日-{end_dt.day}日"

        cover_idx = media_count // 2
        cover_media_id = cluster[cover_idx][0]

        cursor = conn.execute(
            "INSERT INTO events (title, start_date, end_date, cover_media_id, media_count) "
            "VALUES (?, ?, ?, ?, ?)",
            (title, start_dt.isoformat(), end_dt.isoformat(), cover_media_id, media_count),
        )
        event_id = cursor.lastrowid

        for sort_order, (media_id, _) in enumerate(cluster):
            conn.execute(
                "INSERT INTO event_media (event_id, media_id, sort_order) "
                "VALUES (?, ?, ?)",
                (event_id, media_id, sort_order),
            )

    conn.commit()
    conn.close()
    return len(clusters)
