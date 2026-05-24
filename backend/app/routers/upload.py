# backend/app/routers/upload.py
import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.config import settings
from app.services.upload_service import handle_uploaded_files

router = APIRouter(prefix="/api/media", tags=["upload"])

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_FILES = 100

ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif",
    ".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v",
}


@router.post("/upload")
async def upload_files(files: list[UploadFile] = File(..., max_length=MAX_FILES)):
    if not files:
        raise HTTPException(status_code=422, detail="No files provided")

    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"最多上传 {MAX_FILES} 张")

    upload_dir = os.path.join(settings.media_root, "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    saved_paths = []
    original_names = []
    for f in files:
        ext = os.path.splitext(f.filename or "")[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            continue

        safe_name = f"{uuid.uuid4().hex}{ext}"
        dest = os.path.join(upload_dir, safe_name)
        content = await f.read()
        if len(content) > MAX_FILE_SIZE:
            continue
        with open(dest, "wb") as out:
            out.write(content)
        saved_paths.append(dest)
        original_names.append(f.filename)

    if not saved_paths:
        raise HTTPException(status_code=400, detail="未保存任何文件，检查格式或大小")

    results = handle_uploaded_files(saved_paths, original_names)
    return {"uploaded": results, "failed": [], "processing": True}
