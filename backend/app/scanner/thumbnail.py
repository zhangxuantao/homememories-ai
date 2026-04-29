# backend/app/scanner/thumbnail.py
import os
from PIL import Image


def generate_thumbnail(
    filepath: str, thumb_dir: str, source_root: str, size: int = 300
) -> str:
    img = Image.open(filepath)
    img.thumbnail((size, size))

    rel_path = os.path.relpath(filepath, source_root)
    thumb_path = os.path.join(thumb_dir, rel_path + ".jpg")
    os.makedirs(os.path.dirname(thumb_path), exist_ok=True)

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.save(thumb_path, "JPEG", quality=80)
    return thumb_path
