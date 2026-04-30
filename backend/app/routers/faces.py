# backend/app/routers/faces.py
from fastapi import APIRouter, Query, HTTPException

router = APIRouter(prefix="/api/faces", tags=["faces"])


@router.get("/clusters")
def get_clusters():
    return []


@router.get("/cluster/{cluster_id}/media")
def get_cluster_media(
    cluster_id: int,
    cursor: str | None = Query(None),
    limit: int = Query(100, le=500),
):
    return {"items": [], "next_cursor": None}


@router.patch("/cluster/{cluster_id}")
def update_cluster_label(cluster_id: int, label: str):
    raise HTTPException(status_code=501, detail="Not implemented yet -- Phase 3")
