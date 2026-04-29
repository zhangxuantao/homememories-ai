# backend/app/scanner/exif_extractor.py
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS


def extract_date_taken(filepath: str) -> str | None:
    try:
        img = Image.open(filepath)
        exif = img._getexif()
        if exif:
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == "DateTimeOriginal":
                    dt = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                    return dt.isoformat()
    except Exception:
        return None
    return None
