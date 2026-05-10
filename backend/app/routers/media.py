# backend/app/routers/media.py
from fastapi import APIRouter, Query, HTTPException
from app.services.media_service import (
    get_media_by_id,
    get_media_random,
    get_media_on_this_day,
    get_similar_media,
    delete_media,
)

router = APIRouter(prefix="/api/media", tags=["media"])


@router.get("/random")
def random_media(
    count: int = Query(4, ge=1, le=20),
    exclude: str | None = Query(None),
):
    exclude_ids = []
    if exclude:
        exclude_ids = [int(x) for x in exclude.split(",") if x.strip().isdigit()]
    items = get_media_random(count=count, exclude_ids=exclude_ids)
    return [item.model_dump() for item in items]


@router.get("/on-this-day")
def on_this_day(
    month: int = Query(..., ge=1, le=12),
    day: int = Query(..., ge=1, le=31),
):
    items = get_media_on_this_day(month=month, day=day)
    return [item.model_dump() for item in items]


@router.get("/{media_id}/similar")
def get_similar(media_id: int, limit: int = Query(20, le=100)):
    items = get_similar_media(media_id, limit=limit)
    return [item.model_dump() for item in items]


@router.get("/{media_id}")
def get_media(media_id: int):
    item = get_media_by_id(media_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Media not found")
    return item.model_dump()


@router.delete("/{media_id}")
def delete_media_endpoint(media_id: int):
    success = delete_media(media_id)
    if not success:
        raise HTTPException(status_code=404, detail="Media not found")
    return {"deleted": True}
