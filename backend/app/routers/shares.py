# backend/app/routers/shares.py
import secrets
import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_connection

router = APIRouter(prefix="/api/shares", tags=["shares"])


class ShareCreate(BaseModel):
    media_ids: list[int]
    title: str | None = None
    expires_in_hours: int | None = None


def _share_row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "token": row["token"],
        "title": row["title"],
        "media_ids": json.loads(row["media_ids"]),
        "expires_at": row["expires_at"],
        "is_active": bool(row["is_active"]),
        "created_at": row["created_at"],
    }


@router.post("")
def create_share(body: ShareCreate):
    if not body.media_ids:
        raise HTTPException(status_code=400, detail="至少选择一张照片")

    token = secrets.token_urlsafe(12)
    now = datetime.now(timezone.utc).isoformat()
    expires_at = None
    if body.expires_in_hours:
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=body.expires_in_hours)).isoformat()

    conn = get_connection()
    conn.execute(
        "INSERT INTO shares (token, title, media_ids, expires_at, is_active, created_at) "
        "VALUES (?, ?, ?, ?, 1, ?)",
        (token, body.title, json.dumps(body.media_ids), expires_at, now),
    )
    conn.commit()
    conn.close()

    return {"token": token, "url": f"/share/{token}"}


@router.get("")
def list_shares():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM shares WHERE is_active = 1 ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [_share_row_to_dict(r) for r in rows]


@router.delete("/{share_id}")
def revoke_share(share_id: int):
    conn = get_connection()
    row = conn.execute("SELECT id FROM shares WHERE id = ?", (share_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="分享不存在")

    conn.execute("UPDATE shares SET is_active = 0 WHERE id = ?", (share_id,))
    conn.commit()
    conn.close()
    return {"revoked": share_id}


# Public endpoint (no auth)
public_router = APIRouter(tags=["share"])


@public_router.get("/api/share/{token}")
def view_share(token: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM shares WHERE token = ? AND is_active = 1", (token,)
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="分享不存在或已失效")

    if row["expires_at"]:
        expires_at = datetime.fromisoformat(row["expires_at"])
        if expires_at < datetime.now(timezone.utc):
            conn.close()
            raise HTTPException(status_code=410, detail="分享链接已过期")

    media_ids = json.loads(row["media_ids"])
    placeholders = ",".join("?" * len(media_ids))
    media_rows = conn.execute(
        f"SELECT id, filename, width, height, media_type, thumbnail_path, date_taken "
        f"FROM media WHERE id IN ({placeholders})",
        media_ids,
    ).fetchall()
    conn.close()

    return {
        "title": row["title"],
        "expires_at": row["expires_at"],
        "created_at": row["created_at"],
        "media": [
            {
                "id": m["id"],
                "filename": m["filename"],
                "width": m["width"],
                "height": m["height"],
                "media_type": m["media_type"],
                "thumbnail_path": m["thumbnail_path"],
                "date_taken": m["date_taken"],
            }
            for m in media_rows
        ],
    }
