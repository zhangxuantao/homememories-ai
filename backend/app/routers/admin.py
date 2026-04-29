# backend/app/routers/admin.py
from fastapi import APIRouter, Query, HTTPException
from app.services.scan_service import (
    start_scan_job,
    get_scan_status,
    get_system_stats,
)

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
