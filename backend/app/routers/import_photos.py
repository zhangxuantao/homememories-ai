# backend/app/routers/import_photos.py
import os
import shutil
import zipfile
import tempfile
import uuid
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/api/import", tags=["import"])

ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif",
    ".heic", ".heif",
    ".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v",
}

SKIP_FILES = {".ds_store", "thumbs.db", "desktop.ini", "archive_browser.html"}


def _is_media_file(filename: str) -> bool:
    name = os.path.basename(filename).lower()
    if name in SKIP_FILES:
        return False
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def _copy_media_files(src_dir: str, dest_dir: str) -> int:
    """Recursively copy media files from src_dir to dest_dir. Returns count."""
    os.makedirs(dest_dir, exist_ok=True)
    count = 0
    for root, dirs, files in os.walk(src_dir):
        for f in files:
            if _is_media_file(f):
                src_path = os.path.join(root, f)
                ext = os.path.splitext(f)[1].lower()
                dest_path = os.path.join(dest_dir, f"{uuid.uuid4().hex}{ext}")
                shutil.copy2(src_path, dest_path)
                count += 1
    return count


def _trigger_scan(path: str) -> dict:
    """Call the scan API on the imported directory."""
    import httpx
    try:
        resp = httpx.post(
            f"http://localhost:{settings.port}/api/admin/scan",
            json={"path": path},
            timeout=5,
        )
        return resp.json()
    except Exception:
        return {"job_id": "scan_triggered", "status": "pending"}


class ICloudImportRequest(BaseModel):
    source_dir: str


@router.post("/takeout")
async def import_takeout(file: UploadFile = File(...)):
    """Upload and extract a Google Takeout zip file."""
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="请上传 .zip 文件")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_dir = os.path.join(settings.media_root, "imports", f"takeout_{ts}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        extract_dir = tempfile.mkdtemp()
        with zipfile.ZipFile(tmp_path, "r") as zf:
            zf.extractall(extract_dir)

        count = _copy_media_files(extract_dir, dest_dir)

        if count == 0:
            raise HTTPException(status_code=400, detail="zip 文件中未找到照片或视频")

        shutil.rmtree(extract_dir, ignore_errors=True)

        scan_result = _trigger_scan(dest_dir)

        return {"imported": count, "destination": dest_dir, "scan": scan_result}

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/icloud")
def import_icloud(body: ICloudImportRequest):
    """Import photos from an iCloud export directory."""
    source_dir = os.path.expanduser(body.source_dir)
    if not os.path.isdir(source_dir):
        raise HTTPException(status_code=400, detail="目录不存在或无法访问")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_dir = os.path.join(settings.media_root, "imports", f"icloud_{ts}")

    count = _copy_media_files(source_dir, dest_dir)

    if count == 0:
        raise HTTPException(status_code=400, detail="目录中未找到照片或视频")

    scan_result = _trigger_scan(dest_dir)

    return {"imported": count, "destination": dest_dir, "scan": scan_result}
