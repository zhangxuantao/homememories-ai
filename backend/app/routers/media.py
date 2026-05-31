# backend/app/routers/media.py
import os
import math
import zipfile
import io
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from app.services.media_service import (
    get_media_by_id,
    get_media_random,
    get_media_on_this_day,
    get_similar_media,
    delete_media,
)

router = APIRouter(prefix="/api/media", tags=["media"])


@router.get("/{media_id}/file")
def serve_original_file(media_id: int):
    """Serve the original media file by media ID (supports video streaming)."""
    item = get_media_by_id(media_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Media not found")
    path = item.path
    if not os.path.isabs(path):
        from app.config import settings
        path = os.path.join(settings.media_root, path)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(path, media_type="application/octet-stream")


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


@router.post("/export-zip")
def export_zip(ids: list[int]):
    """Stream selected media as a zip file download."""
    from app.database import get_connection
    from app.config import settings

    conn = get_connection()
    placeholders = ",".join("?" * len(ids))
    rows = conn.execute(
        f"SELECT id, path, filename FROM media WHERE id IN ({placeholders})",
        ids,
    ).fetchall()
    conn.close()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for row in rows:
            path = row["path"]
            if not os.path.isabs(path):
                path = os.path.join(settings.media_root, path)
            filename = row["filename"]
            if os.path.exists(path):
                zf.write(path, f"{row['id']}_{filename}")

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=homememories_export.zip"},
    )


from pydantic import BaseModel as PydanticModel

class CollageRequest(PydanticModel):
    media_ids: list[int]
    layout: str = "grid"


@router.post("/collage")
def create_collage(body: CollageRequest):
    """Generate a photo collage from selected media."""
    from app.database import get_connection
    from app.config import settings
    from PIL import Image
    import io as io_module
    import math as math_module

    if not body.media_ids:
        raise HTTPException(status_code=400, detail="至少选择一张照片")

    if len(body.media_ids) > 9:
        raise HTTPException(status_code=400, detail="最多选择9张照片")

    conn = get_connection()
    placeholders = ",".join("?" * len(body.media_ids))
    rows = conn.execute(
        f"SELECT id, path FROM media WHERE id IN ({placeholders})", body.media_ids
    ).fetchall()
    conn.close()

    if len(rows) != len(body.media_ids):
        raise HTTPException(status_code=404, detail="部分照片不存在")

    # Load images
    images = []
    for row in rows:
        path = row["path"]
        if not os.path.isabs(path):
            path = os.path.join(settings.media_root, path)
        if os.path.exists(path):
            img = Image.open(path).convert("RGB")
            img.thumbnail((400, 400), Image.LANCZOS)
            images.append(img)

    if not images:
        raise HTTPException(status_code=404, detail="无法加载任何照片")

    layout = body.layout
    n = len(images)

    if layout == "horizontal":
        h = min(img.height for img in images)
        resized = []
        for img in images:
            ratio = h / img.height
            new_w = int(img.width * ratio)
            resized.append(img.resize((new_w, h), Image.LANCZOS))
        total_w = sum(img.width for img in resized)
        canvas = Image.new("RGB", (total_w, h), "white")
        x = 0
        for img in resized:
            canvas.paste(img, (x, 0))
            x += img.width

    elif layout == "vertical":
        w = min(img.width for img in images)
        resized = []
        for img in images:
            ratio = w / img.width
            new_h = int(img.height * ratio)
            resized.append(img.resize((w, new_h), Image.LANCZOS))
        total_h = sum(img.height for img in resized)
        canvas = Image.new("RGB", (w, total_h), "white")
        y = 0
        for img in resized:
            canvas.paste(img, (0, y))
            y += img.height

    else:  # grid
        cols = math_module.ceil(math_module.sqrt(n))
        rows_count = math_module.ceil(n / cols)
        cell_w = min(img.width for img in images)
        cell_h = min(img.height for img in images)

        resized = [img.resize((cell_w, cell_h), Image.LANCZOS) for img in images]

        canvas = Image.new("RGB", (cols * cell_w, rows_count * cell_h), "white")
        for i, img in enumerate(resized):
            r = i // cols
            c = i % cols
            canvas.paste(img, (c * cell_w, r * cell_h))

    buf = io_module.BytesIO()
    canvas.save(buf, format="JPEG", quality=90)
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/jpeg")
