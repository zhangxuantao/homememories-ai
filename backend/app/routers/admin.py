# backend/app/routers/admin.py
from fastapi import APIRouter, Query, HTTPException
from app.services.scan_service import (
    start_scan_job,
    get_scan_status,
    get_system_stats,
)
from app.services.search_service import generate_embeddings
from app.services.quality_service import (
    run_blur_check,
    run_duplicate_check,
    get_blurry_media,
    get_duplicate_pairs,
)
from app.services.media_service import delete_media
from app.services.face_service import start_face_detection

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/scan")
def start_scan():
    job_id = start_scan_job()
    status = get_scan_status(job_id)
    return status.model_dump()


@router.get("/scan/status")
def scan_status(job_id: str = Query(...)):
    result = get_scan_status(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return result.model_dump()


@router.get("/stats")
def system_stats():
    return get_system_stats().model_dump()


@router.post("/embeddings/generate")
def start_embedding_generation():
    job_id = generate_embeddings()
    from app.services.scan_service import get_job_status
    status = get_job_status(job_id)
    return status.model_dump()


# ── Cleanup / Quality endpoints ──────────────────────────────────────────────


@router.post("/cleanup/blurry/check")
def start_blur_check():
    job_id = run_blur_check()
    from app.services.scan_service import get_job_status
    return get_job_status(job_id).model_dump()


@router.post("/cleanup/duplicates/check")
def start_duplicate_check():
    job_id = run_duplicate_check()
    from app.services.scan_service import get_job_status
    return get_job_status(job_id).model_dump()


@router.get("/cleanup/blurry")
def list_blurry_media(threshold: float = 100.0, limit: int = 50):
    items = get_blurry_media(threshold=threshold, limit=limit)
    return [item.model_dump() for item in items]


@router.get("/cleanup/duplicates")
def list_duplicates():
    pairs = get_duplicate_pairs()
    return [[m1.model_dump(), m2.model_dump()] for m1, m2 in pairs]


@router.delete("/cleanup/blurry")
def delete_blurry_media(ids: list[int]):
    deleted = []
    for media_id in ids:
        success = delete_media(media_id)
        deleted.append({"id": media_id, "deleted": success})
    return {"deleted": deleted}


# ── Face Detection ──────────────────────────────────────────────────────────


@router.post("/faces/detect")
def start_face_detection_endpoint():
    job_id = start_face_detection()
    from app.services.scan_service import get_job_status
    return get_job_status(job_id).model_dump()
