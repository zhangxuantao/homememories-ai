# backend/app/routers/search.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.search_service import search_by_text, search_by_image
from app.models import SearchRequest

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("/text")
def text_search(request: SearchRequest):
    if not request.query.strip():
        raise HTTPException(status_code=422, detail="Query must not be empty")
    return search_by_text(
        query=request.query,
        limit=request.limit,
        cursor=int(request.cursor or 0),
    )


@router.post("/image")
def image_search(image_file: UploadFile = File(...)):
    if not image_file.content_type or not image_file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = image_file.file.read()
    results = search_by_image(image_bytes)
    return {"results": results}
