# backend/tests/conftest.py
import pytest
import os
import shutil
from app.database import init_db, get_connection
from app.config import Settings


@pytest.fixture
def tmp_db_path(tmp_path):
    """Creates a temporary database with schema already applied."""
    db_path = str(tmp_path / "metadata.db")
    init_db(db_path)
    return db_path


@pytest.fixture
def tmp_conn(tmp_db_path):
    """Returns a connection to the temporary database."""
    conn = get_connection(tmp_db_path)
    yield conn
    conn.close()


@pytest.fixture
def tmp_settings(tmp_path, monkeypatch):
    """Overrides settings to use temp directories."""
    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path / "media"))
    monkeypatch.setenv("DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setenv("THUMBNAIL_SIZE", "300")
    from app.config import settings

    return settings


@pytest.fixture
def test_image(tmp_path):
    """Creates a simple test JPEG with EXIF DateTimeOriginal tag."""
    from PIL import Image
    from PIL.ExifTags import Base

    img = Image.new("RGB", (800, 600), color=(255, 200, 200))
    img_path = str(tmp_path / "test_photo.jpg")
    exif = img.getexif()
    exif[Base.DateTimeOriginal] = "2025:05:15 14:30:00"
    img.save(img_path, "JPEG", exif=exif.tobytes())
    return img_path


@pytest.fixture
def test_image_no_exif(tmp_path):
    """Creates a test JPEG without EXIF data."""
    from PIL import Image

    img = Image.new("RGB", (400, 300), color=(100, 150, 200))
    img_path = str(tmp_path / "no_exif.jpg")
    img.save(img_path, "JPEG")
    return img_path
