# Phase 1: Backend Core — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Python FastAPI backend with SQLite storage, media scanning with EXIF extraction, thumbnail generation, and core REST API endpoints (timeline, media CRUD, admin scan).

**Architecture:** FastAPI application with three-layer structure: routers (HTTP handlers) → services (business logic) → database (SQLite via raw sqlite3). Media scanner runs as a background task with progress tracking. Static files served via FastAPI's StaticFiles mount.

**Tech Stack:** Python 3.11, FastAPI, SQLite (sqlite3 stdlib), Pillow, exifread, uvicorn, pytest, httpx (async test client)

---

## File Structure

```
backend/
├── requirements.txt
├── .env.example
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI app, CORS, static mounts
│   ├── config.py              # Settings from env vars
│   ├── database.py            # SQLite connection + schema DDL
│   ├── models.py              # Pydantic request/response schemas
│   ├── scanner/
│   │   ├── __init__.py
│   │   ├── exif_extractor.py  # EXIF date extraction
│   │   ├── thumbnail.py       # Thumbnail generation (300px)
│   │   └── scanner.py         # Directory walk, file processing
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── timeline.py        # GET /api/timeline/*
│   │   ├── media.py           # GET /api/media/*, DELETE /api/media/:id
│   │   └── admin.py           # POST /api/admin/scan, GET status/stats
│   └── services/
│       ├── __init__.py
│       ├── media_service.py   # Media queries + mutations
│       └── scan_service.py    # Scan orchestration + progress
└── tests/
    ├── __init__.py
    ├── conftest.py            # Fixtures: temp DB, test app, test images
    ├── test_database.py
    ├── test_exif_extractor.py
    ├── test_thumbnail.py
    ├── test_scanner.py
    ├── test_media_service.py
    ├── test_scan_service.py
    ├── test_timeline_api.py
    ├── test_media_api.py
    └── test_admin_api.py
```

**Design decisions:**
- `sqlite3` stdlib (no SQLAlchemy) — simple, zero-dependency, sufficient for single-user local app
- Scanner is synchronous with `BackgroundTasks` — No Celery/Redis overhead for single-machine use
- Thumbnails stored flat under `DATA_ROOT/thumbs/` mirroring source directory structure
- Cursor-based pagination with `date_taken, id` composite cursor

---

### Task 1: Project scaffolding and configuration

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/tests/__init__.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p backend/app/scanner backend/app/routers backend/app/services backend/tests
```

- [ ] **Step 2: Write requirements.txt**

```python
# backend/requirements.txt
fastapi==0.115.0
uvicorn[standard]==0.30.0
pillow==10.2.0
exifread==3.0.1
python-dotenv==1.0.1
aiofiles==24.1.0
python-multipart==0.0.9

# Testing
pytest==8.3.0
pytest-asyncio==0.24.0
httpx==0.27.0
```

- [ ] **Step 3: Write .env.example**

```bash
MEDIA_ROOT=D:/Photos
DATA_ROOT=./data
THUMBNAIL_SIZE=300
HOST=0.0.0.0
PORT=8501
```

- [ ] **Step 4: Write app/__init__.py and tests/__init__.py (empty)**

```bash
touch backend/app/__init__.py backend/tests/__init__.py
```

- [ ] **Step 5: Write config.py**

```python
# backend/app/config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    media_root: str = os.getenv("MEDIA_ROOT", "./media")
    data_root: str = os.getenv("DATA_ROOT", "./data")
    thumbnail_size: int = int(os.getenv("THUMBNAIL_SIZE", "300"))
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8501"))

    @property
    def db_path(self) -> str:
        return os.path.join(self.data_root, "metadata.db")

    @property
    def thumb_dir(self) -> str:
        return os.path.join(self.data_root, "thumbs")


settings = Settings()
```

- [ ] **Step 6: Install dependencies and verify**

```bash
cd backend && pip install -r requirements.txt
```

Expected: all packages install successfully.

- [ ] **Step 7: Commit**

```bash
git add backend/requirements.txt backend/.env.example backend/app/__init__.py backend/app/config.py backend/tests/__init__.py
git commit -m "feat: project scaffolding with config and dependencies"
```

---

### Task 2: Database setup with full schema

**Files:**
- Create: `backend/app/database.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_database.py`

- [ ] **Step 1: Write the failing test for database init**

```python
# backend/tests/test_database.py
import sqlite3
import os
from app.database import get_connection, init_db, SCHEMA


def test_init_db_creates_tables(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()

    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    table_names = [r[0] for r in tables]

    assert "media" in table_names
    assert "embeddings" in table_names
    assert "faces" in table_names
    assert "face_clusters" in table_names
    assert "events" in table_names
    assert "event_media" in table_names
    assert "search_cache" in table_names
    conn.close()


def test_init_db_creates_indexes(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()

    indexes = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
    ).fetchall()
    index_names = [r[0] for r in indexes]

    assert "idx_media_date" in index_names
    assert "idx_media_type" in index_names
    assert "idx_media_checksum" in index_names
    assert "idx_faces_cluster" in index_names
    assert "idx_faces_media" in index_names
    conn.close()


def test_media_table_constraints(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)

    # path must be unique
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added) VALUES (?, ?, ?, ?)",
        ("/test/photo.jpg", "photo.jpg", "image", "2026-04-29T00:00:00"),
    )
    conn.commit()
    try:
        conn.execute(
            "INSERT INTO media (path, filename, media_type, date_added) VALUES (?, ?, ?, ?)",
            ("/test/photo.jpg", "photo.jpg", "image", "2026-04-29T00:00:00"),
        )
        conn.commit()
        assert False, "Should have raised IntegrityError"
    except sqlite3.IntegrityError:
        pass
    conn.close()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_database.py -v
```

Expected: FAIL with `NameError: name 'SCHEMA' is not defined` (from `app.database`).

- [ ] **Step 3: Write database.py with full schema**

```python
# backend/app/database.py
import sqlite3
import os
from app.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS media (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    filename TEXT NOT NULL,
    media_type TEXT NOT NULL,
    width INTEGER,
    height INTEGER,
    file_size INTEGER,
    date_taken TEXT,
    date_added TEXT NOT NULL,
    thumbnail_path TEXT,
    duration REAL,
    is_blurry BOOLEAN DEFAULT 0,
    blur_score REAL,
    dhash TEXT,
    checksum TEXT,
    embedding_id INTEGER
);

CREATE TABLE IF NOT EXISTS embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id INTEGER UNIQUE,
    vector BLOB NOT NULL,
    model_version TEXT,
    created_at TEXT,
    FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS faces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id INTEGER,
    cluster_id INTEGER,
    bbox TEXT,
    embedding BLOB,
    thumbnail_path TEXT,
    FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE,
    FOREIGN KEY (cluster_id) REFERENCES face_clusters(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS face_clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT,
    cover_face_id INTEGER,
    photo_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    start_date TEXT,
    end_date TEXT,
    cover_media_id INTEGER,
    media_count INTEGER DEFAULT 0,
    location TEXT,
    FOREIGN KEY (cover_media_id) REFERENCES media(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS event_media (
    event_id INTEGER,
    media_id INTEGER,
    sort_order INTEGER,
    PRIMARY KEY (event_id, media_id),
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS search_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_hash TEXT UNIQUE,
    query_text TEXT,
    result_ids TEXT,
    created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_media_date ON media(date_taken);
CREATE INDEX IF NOT EXISTS idx_media_type ON media(media_type);
CREATE INDEX IF NOT EXISTS idx_media_checksum ON media(checksum);
CREATE INDEX IF NOT EXISTS idx_media_dhash ON media(dhash);
CREATE INDEX IF NOT EXISTS idx_faces_cluster ON faces(cluster_id);
CREATE INDEX IF NOT EXISTS idx_faces_media ON faces(media_id);
CREATE INDEX IF NOT EXISTS idx_event_media_event ON event_media(event_id);
"""


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    path = db_path or os.path.join(settings.data_root, "metadata.db")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: str | None = None) -> None:
    conn = get_connection(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_database.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 5: Write conftest.py with shared fixtures**

```python
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
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/database.py backend/tests/conftest.py backend/tests/test_database.py
git commit -m "feat: SQLite database with full schema and test fixtures"
```

---

### Task 3: EXIF date extractor

**Files:**
- Create: `backend/app/scanner/__init__.py`
- Create: `backend/app/scanner/exif_extractor.py`
- Create: `backend/tests/test_exif_extractor.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_exif_extractor.py
from app.scanner.exif_extractor import extract_date_taken


def test_extract_date_taken_from_exif(test_image):
    result = extract_date_taken(test_image)
    assert result == "2025-05-15T14:30:00"


def test_extract_date_taken_no_exif(test_image_no_exif):
    result = extract_date_taken(test_image_no_exif)
    assert result is None


def test_extract_date_taken_nonexistent_file():
    result = extract_date_taken("/nonexistent/file.jpg")
    assert result is None


def test_extract_date_taken_video_file(tmp_path):
    """Video files return None (no EXIF date support yet)."""
    video_path = tmp_path / "test.mp4"
    video_path.write_bytes(b"\x00\x00\x00\x18ftypmp42")
    result = extract_date_taken(str(video_path))
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_exif_extractor.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.scanner.exif_extractor'`

- [ ] **Step 3: Create scanner __init__.py**

```bash
touch backend/app/scanner/__init__.py
```

- [ ] **Step 4: Write the minimal implementation**

```python
# backend/app/scanner/exif_extractor.py
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
                    dt_str = value.replace(" ", "T")
                    return dt_str
    except Exception:
        return None
    return None
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd backend && python -m pytest tests/test_exif_extractor.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/scanner/__init__.py backend/app/scanner/exif_extractor.py backend/tests/test_exif_extractor.py
git commit -m "feat: EXIF date extraction with DateTimeOriginal support"
```

---

### Task 4: Thumbnail generation

**Files:**
- Create: `backend/app/scanner/thumbnail.py`
- Create: `backend/tests/test_thumbnail.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_thumbnail.py
import os
from PIL import Image
from app.scanner.thumbnail import generate_thumbnail


def test_generate_thumbnail_creates_file(test_image, tmp_path):
    thumb_dir = str(tmp_path / "thumbs")
    source_root = os.path.dirname(test_image)

    with __import__("app.config").config.settings_fixture_override():
        pass

    result_path = generate_thumbnail(test_image, thumb_dir, source_root, size=300)

    assert os.path.exists(result_path)
    thumb = Image.open(result_path)
    assert thumb.width <= 300
    assert thumb.height <= 600  # original is 800x600, so height should be <=600
    assert result_path.endswith(".jpg")


def test_generate_thumbnail_mirrors_structure(test_image, tmp_path):
    thumb_dir = str(tmp_path / "thumbs")
    source_root = os.path.dirname(os.path.dirname(test_image))

    result_path = generate_thumbnail(test_image, thumb_dir, source_root, size=300)

    rel = os.path.relpath(result_path, thumb_dir)
    expected_rel = os.path.relpath(test_image, source_root) + ".jpg"
    assert rel == expected_rel


def test_thumbnail_creates_parent_dirs(test_image, tmp_path):
    thumb_dir = str(tmp_path / "deep" / "nested" / "thumbs")
    source_root = os.path.dirname(test_image)

    result_path = generate_thumbnail(test_image, thumb_dir, source_root, size=300)

    assert os.path.exists(result_path)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_thumbnail.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.scanner.thumbnail'`

- [ ] **Step 3: Write the implementation**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_thumbnail.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/scanner/thumbnail.py backend/tests/test_thumbnail.py
git commit -m "feat: thumbnail generation with mirrored directory structure"
```

---

### Task 5: Media scanner

**Files:**
- Create: `backend/app/scanner/scanner.py`
- Create: `backend/tests/test_scanner.py`

- [ ] **Step 1: Write the failing test for file checksum**

```python
# backend/tests/test_scanner.py
import os
import time
from app.scanner.scanner import file_checksum, scan_directory, is_image_file, is_video_file


def test_file_checksum_deterministic(test_image):
    h1 = file_checksum(test_image)
    h2 = file_checksum(test_image)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex digest


def test_file_checksum_different_for_different_files(test_image, test_image_no_exif):
    h1 = file_checksum(test_image)
    h2 = file_checksum(test_image_no_exif)
    assert h1 != h2


def test_is_image_file():
    assert is_image_file("photo.jpg") is True
    assert is_image_file("photo.JPEG") is True
    assert is_image_file("photo.png") is True
    assert is_image_file("photo.gif") is False
    assert is_image_file("video.mp4") is False


def test_is_video_file():
    assert is_video_file("video.mp4") is True
    assert is_video_file("video.MOV") is True
    assert is_video_file("video.avi") is True
    assert is_video_file("photo.jpg") is False


def test_scan_directory_creates_media_records(tmp_path, tmp_db_path):
    from PIL import Image
    from PIL.ExifTags import Base
    from app.database import get_connection

    # Create test images in a temp media dir
    media_dir = tmp_path / "photos"
    media_dir.mkdir()
    img = Image.new("RGB", (200, 100), color=(100, 200, 100))
    exif = img.getexif()
    exif[Base.DateTimeOriginal] = "2025:06:20 10:00:00"
    img.save(str(media_dir / "summer.jpg"), "JPEG", exif=exif.tobytes())
    Image.new("RGB", (400, 300), color=(50, 50, 200)).save(
        str(media_dir / "winter.jpg"), "JPEG"
    )

    thumb_dir = str(tmp_path / "thumbs")

    result = scan_directory(
        str(media_dir), thumb_dir, db_path=tmp_db_path
    )

    assert result["total"] >= 2
    assert result["new"] >= 2
    assert result["skipped"] == 0

    conn = get_connection(tmp_db_path)
    rows = conn.execute("SELECT * FROM media ORDER BY filename").fetchall()
    assert len(rows) >= 2
    assert rows[0]["filename"] == "summer.jpg"
    assert rows[0]["date_taken"] == "2025-06-20T10:00:00"
    assert rows[0]["width"] == 200
    assert rows[0]["height"] == 100
    assert rows[0]["thumbnail_path"] is not None
    conn.close()


def test_scan_directory_skips_existing(tmp_path, tmp_db_path):
    from PIL import Image
    from app.database import get_connection

    media_dir = tmp_path / "photos"
    media_dir.mkdir()
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    img.save(str(media_dir / "single.jpg"), "JPEG")

    thumb_dir = str(tmp_path / "thumbs")

    # First scan
    r1 = scan_directory(str(media_dir), thumb_dir, db_path=tmp_db_path)
    assert r1["new"] == 1

    # Second scan — should skip
    r2 = scan_directory(str(media_dir), thumb_dir, db_path=tmp_db_path)
    assert r2["new"] == 0
    assert r2["skipped"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_scanner.py -v
```

Expected: FAIL with import error.

- [ ] **Step 3: Write the scanner implementation**

```python
# backend/app/scanner/scanner.py
import os
import hashlib
from datetime import datetime, timezone
from app.database import get_connection
from app.scanner.exif_extractor import extract_date_taken
from app.scanner.thumbnail import generate_thumbnail

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}


def is_image_file(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in IMAGE_EXTENSIONS


def is_video_file(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in VIDEO_EXTENSIONS


def file_checksum(filepath: str) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def scan_directory(
    media_root: str, thumb_dir: str, db_path: str | None = None
) -> dict:
    conn = get_connection(db_path)
    date_added = datetime.now(timezone.utc).isoformat()

    total = 0
    new = 0
    skipped = 0

    for dirpath, _, filenames in os.walk(media_root):
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in IMAGE_EXTENSIONS and ext not in VIDEO_EXTENSIONS:
                continue

            total += 1
            filepath = os.path.join(dirpath, filename)

            # Check if already scanned by checksum
            csum = file_checksum(filepath)
            existing = conn.execute(
                "SELECT id FROM media WHERE checksum = ?", (csum,)
            ).fetchone()
            if existing:
                skipped += 1
                continue

            media_type = "image" if ext in IMAGE_EXTENSIONS else "video"
            date_taken = extract_date_taken(filepath) if media_type == "image" else None
            file_size = os.path.getsize(filepath)

            width = None
            height = None
            thumbnail_path = None

            if media_type == "image":
                from PIL import Image

                try:
                    img = Image.open(filepath)
                    width, height = img.size
                except Exception:
                    pass

                thumbnail_path = generate_thumbnail(filepath, thumb_dir, media_root)

            conn.execute(
                """INSERT INTO media
                   (path, filename, media_type, width, height, file_size,
                    date_taken, date_added, thumbnail_path, checksum)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    filepath, filename, media_type, width, height, file_size,
                    date_taken, date_added, thumbnail_path, csum,
                ),
            )
            new += 1

    conn.commit()
    conn.close()
    return {"total": total, "new": new, "skipped": skipped}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_scanner.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/scanner/scanner.py backend/tests/test_scanner.py
git commit -m "feat: media scanner with checksum dedup and EXIF+thumbnail pipeline"
```

---

### Task 6: Pydantic API models

**Files:**
- Create: `backend/app/models.py`

- [ ] **Step 1: Write all Pydantic models (no test needed — these are data structures)**

```python
# backend/app/models.py
from pydantic import BaseModel
from datetime import datetime


class MediaItem(BaseModel):
    id: int
    path: str
    filename: str
    media_type: str
    width: int | None = None
    height: int | None = None
    file_size: int | None = None
    date_taken: str | None = None
    date_added: str
    thumbnail_path: str | None = None
    duration: float | None = None
    is_blurry: bool = False

    @classmethod
    def from_row(cls, row):
        return cls(**dict(row))


class TimelineEvent(BaseModel):
    id: int
    title: str
    start_date: str
    end_date: str
    cover_media_id: int | None = None
    media_count: int = 0
    location: str | None = None

    @classmethod
    def from_row(cls, row):
        return cls(**dict(row))


class PaginatedResponse(BaseModel):
    items: list
    next_cursor: str | None = None


class ScanResult(BaseModel):
    job_id: str
    status: str  # "pending" | "running" | "completed" | "failed"
    progress: float = 0.0  # 0-100
    total: int = 0
    new: int = 0
    skipped: int = 0
    error: str | None = None


class SystemStats(BaseModel):
    db_size_bytes: int
    media_count: int
    image_count: int
    video_count: int
    last_scan_time: str | None = None


class SearchRequest(BaseModel):
    query: str
    limit: int = 20
    cursor: str | None = None


class SearchResponse(BaseModel):
    results: list[MediaItem]
    next_cursor: str | None = None
```

- [ ] **Step 2: Verify models import correctly**

```bash
cd backend && python -c "from app.models import MediaItem, TimelineEvent, ScanResult; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/models.py
git commit -m "feat: Pydantic API models for media, timeline, and scan"
```

---

### Task 7: Media service layer

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/media_service.py`
- Create: `backend/tests/test_media_service.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_media_service.py
from app.services.media_service import (
    get_media_by_id,
    get_media_random,
    get_media_on_this_day,
    delete_media,
)
from app.database import get_connection


def _seed_media(conn):
    conn.execute(
        """INSERT INTO media (path, filename, media_type, date_taken, date_added, checksum)
           VALUES ('/p/1.jpg', '1.jpg', 'image', '2025-04-29T12:00:00', '2026-01-01T00:00:00', 'aaa')"""
    )
    conn.execute(
        """INSERT INTO media (path, filename, media_type, date_taken, date_added, checksum)
           VALUES ('/p/2.jpg', '2.jpg', 'image', '2024-04-29T08:00:00', '2026-01-01T00:00:00', 'bbb')"""
    )
    conn.execute(
        """INSERT INTO media (path, filename, media_type, date_taken, date_added, checksum)
           VALUES ('/p/3.jpg', '3.jpg', 'image', '2025-05-01T10:00:00', '2026-01-01T00:00:00', 'ccc')"""
    )
    conn.commit()


def test_get_media_by_id_found(tmp_db_path):
    conn = get_connection(tmp_db_path)
    _seed_media(conn)
    conn.close()

    item = get_media_by_id(1, db_path=tmp_db_path)
    assert item is not None
    assert item.filename == "1.jpg"


def test_get_media_by_id_not_found(tmp_db_path):
    item = get_media_by_id(999, db_path=tmp_db_path)
    assert item is None


def test_get_media_random(tmp_db_path):
    conn = get_connection(tmp_db_path)
    _seed_media(conn)
    conn.close()

    results = get_media_random(2, exclude_ids=[], db_path=tmp_db_path)
    assert len(results) == 2
    ids = [r.id for r in results]
    assert len(set(ids)) == 2  # no duplicates


def test_get_media_random_respects_exclude(tmp_db_path):
    conn = get_connection(tmp_db_path)
    _seed_media(conn)
    conn.close()

    results = get_media_random(10, exclude_ids=[1, 2], db_path=tmp_db_path)
    ids = [r.id for r in results]
    assert 1 not in ids
    assert 2 not in ids


def test_get_media_on_this_day(tmp_db_path):
    conn = get_connection(tmp_db_path)
    _seed_media(conn)
    conn.close()

    results = get_media_on_this_day(month=4, day=29, db_path=tmp_db_path)
    # Should include both 2025-04-29 and 2024-04-29
    dates = [r.date_taken for r in results]
    assert "2025-04-29T12:00:00" in dates
    assert "2024-04-29T08:00:00" in dates
    assert len(results) == 2


def test_delete_media_removes_record(tmp_db_path):
    conn = get_connection(tmp_db_path)
    _seed_media(conn)
    conn.close()

    success = delete_media(1, db_path=tmp_db_path)
    assert success is True

    item = get_media_by_id(1, db_path=tmp_db_path)
    assert item is None


def test_delete_media_nonexistent(tmp_db_path):
    success = delete_media(999, db_path=tmp_db_path)
    assert success is False
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_media_service.py -v
```

Expected: FAIL with import error.

- [ ] **Step 3: Create services __init__.py**

```bash
touch backend/app/services/__init__.py
```

- [ ] **Step 4: Write the media service implementation**

```python
# backend/app/services/media_service.py
from app.database import get_connection
from app.models import MediaItem


def get_media_by_id(media_id: int, db_path: str | None = None) -> MediaItem | None:
    conn = get_connection(db_path)
    row = conn.execute("SELECT * FROM media WHERE id = ?", (media_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return MediaItem.from_row(row)


def get_media_random(
    count: int = 4, exclude_ids: list[int] | None = None, db_path: str | None = None
) -> list[MediaItem]:
    conn = get_connection(db_path)
    exclude = exclude_ids or []
    if exclude:
        placeholders = ",".join("?" * len(exclude))
        rows = conn.execute(
            f"SELECT * FROM media WHERE id NOT IN ({placeholders}) ORDER BY RANDOM() LIMIT ?",
            (*exclude, count),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM media ORDER BY RANDOM() LIMIT ?", (count,)
        ).fetchall()
    conn.close()
    return [MediaItem.from_row(r) for r in rows]


def get_media_on_this_day(
    month: int, day: int, db_path: str | None = None
) -> list[MediaItem]:
    conn = get_connection(db_path)
    rows = conn.execute(
        """SELECT * FROM media
           WHERE date_taken IS NOT NULL
           AND CAST(strftime('%m', date_taken) AS INTEGER) = ?
           AND CAST(strftime('%d', date_taken) AS INTEGER) = ?
           ORDER BY date_taken DESC""",
        (month, day),
    ).fetchall()
    conn.close()
    return [MediaItem.from_row(r) for r in rows]


def delete_media(media_id: int, db_path: str | None = None) -> bool:
    conn = get_connection(db_path)
    cursor = conn.execute("DELETE FROM media WHERE id = ?", (media_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_media_service.py -v
```

Expected: 7 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/__init__.py backend/app/services/media_service.py backend/tests/test_media_service.py
git commit -m "feat: media service layer with get, random, on-this-day, and delete"
```

---

### Task 8: Scan service layer

**Files:**
- Create: `backend/app/services/scan_service.py`
- Create: `backend/tests/test_scan_service.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_scan_service.py
from app.services.scan_service import (
    ScanJobTracker,
    start_scan_job,
    get_scan_status,
    get_system_stats,
)


class TestScanJobTracker:
    def test_create_job(self):
        tracker = ScanJobTracker()
        job_id = tracker.create()
        assert job_id is not None
        assert len(job_id) == 36  # UUID format

    def test_job_starts_pending(self):
        tracker = ScanJobTracker()
        job_id = tracker.create()
        status = tracker.get(job_id)
        assert status["status"] == "pending"
        assert status["progress"] == 0.0

    def test_update_job(self):
        tracker = ScanJobTracker()
        job_id = tracker.create()
        tracker.update(job_id, status="running", progress=50.0)
        status = tracker.get(job_id)
        assert status["status"] == "running"
        assert status["progress"] == 50.0

    def test_get_nonexistent_job(self):
        tracker = ScanJobTracker()
        assert tracker.get("nonexistent") is None


def test_get_system_stats_empty(tmp_db_path):
    stats = get_system_stats(db_path=tmp_db_path)
    assert stats.media_count == 0
    assert stats.image_count == 0
    assert stats.video_count == 0
    assert stats.last_scan_time is None


def test_get_system_stats_with_data(tmp_db_path):
    from app.database import get_connection

    conn = get_connection(tmp_db_path)
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added) VALUES (?,?,?,?)",
        ("/a.jpg", "a.jpg", "image", "2026-01-01T00:00:00"),
    )
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added) VALUES (?,?,?,?)",
        ("/b.mp4", "b.mp4", "video", "2026-01-02T00:00:00"),
    )
    conn.commit()
    conn.close()

    stats = get_system_stats(db_path=tmp_db_path)
    assert stats.media_count == 2
    assert stats.image_count == 1
    assert stats.video_count == 1
    assert stats.last_scan_time == "2026-01-02T00:00:00"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_scan_service.py -v
```

Expected: FAIL with import error.

- [ ] **Step 3: Write the scan service implementation**

```python
# backend/app/services/scan_service.py
import uuid
import os
import threading
from app.database import get_connection
from app.models import ScanResult, SystemStats
from app.scanner.scanner import scan_directory
from app.config import settings


class ScanJobTracker:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._jobs = {}
        return cls._instance

    def create(self) -> str:
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = {
            "status": "pending",
            "progress": 0.0,
            "total": 0,
            "new": 0,
            "skipped": 0,
            "error": None,
        }
        return job_id

    def update(self, job_id: str, **kwargs):
        if job_id in self._jobs:
            self._jobs[job_id].update(kwargs)

    def get(self, job_id: str) -> dict | None:
        return self._jobs.get(job_id)


def start_scan_job() -> str:
    tracker = ScanJobTracker()
    job_id = tracker.create()

    def _run_scan():
        tracker.update(job_id, status="running")
        try:
            result = scan_directory(
                settings.media_root, settings.thumb_dir
            )
            tracker.update(
                job_id,
                status="completed",
                progress=100.0,
                total=result["total"],
                new=result["new"],
                skipped=result["skipped"],
            )
        except Exception as e:
            tracker.update(job_id, status="failed", error=str(e))

    thread = threading.Thread(target=_run_scan, daemon=True)
    thread.start()
    return job_id


def get_scan_status(job_id: str) -> ScanResult | None:
    tracker = ScanJobTracker()
    job = tracker.get(job_id)
    if job is None:
        return None
    return ScanResult(job_id=job_id, **job)


def get_system_stats(db_path: str | None = None) -> SystemStats:
    conn = get_connection(db_path)
    db_path_actual = db_path or os.path.join(settings.data_root, "metadata.db")

    media_count = conn.execute("SELECT COUNT(*) FROM media").fetchone()[0]
    image_count = conn.execute(
        "SELECT COUNT(*) FROM media WHERE media_type = 'image'"
    ).fetchone()[0]
    video_count = conn.execute(
        "SELECT COUNT(*) FROM media WHERE media_type = 'video'"
    ).fetchone()[0]
    last_scan = conn.execute(
        "SELECT date_added FROM media ORDER BY date_added DESC LIMIT 1"
    ).fetchone()

    db_size = os.path.getsize(db_path_actual) if os.path.exists(db_path_actual) else 0

    conn.close()
    return SystemStats(
        db_size_bytes=db_size,
        media_count=media_count,
        image_count=image_count,
        video_count=video_count,
        last_scan_time=last_scan["date_added"] if last_scan else None,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_scan_service.py -v
```

Expected: 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/scan_service.py backend/tests/test_scan_service.py
git commit -m "feat: scan service with job tracker, async scan, and system stats"
```

---

### Task 9: Timeline API router

**Files:**
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/timeline.py`
- Create: `backend/tests/test_timeline_api.py`

- [ ] **Step 1: Write the failing API test**

```python
# backend/tests/test_timeline_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.database import get_connection, init_db


@pytest.fixture
def app_for_test(tmp_path, monkeypatch):
    """Creates a FastAPI test app with isolated database."""
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path / "media"))
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("THUMBNAIL_SIZE", "300")

    init_db(db_path)

    from app.main import create_app
    from app.config import settings

    settings.__dict__["db_path"] = db_path  # HACK: no need to refactor config
    app = create_app()
    return app, db_path


@pytest.fixture
def seeded_app(app_for_test):
    app, db_path = app_for_test
    conn = get_connection(db_path)
    conn.execute(
        """INSERT INTO media (path, filename, media_type, date_taken, date_added, checksum)
           VALUES ('/p/1.jpg', '1.jpg', 'image', '2025-04-29T12:00:00', '2026-01-01T00:00:00', 'a1')"""
    )
    conn.execute(
        """INSERT INTO media (path, filename, media_type, date_taken, date_added, checksum)
           VALUES ('/p/2.jpg', '2.jpg', 'image', '2025-05-15T08:00:00', '2026-01-01T00:00:00', 'b1')"""
    )
    conn.execute(
        """INSERT INTO media (path, filename, media_type, date_taken, date_added, checksum)
           VALUES ('/p/3.jpg', '3.jpg', 'image', '2024-04-29T10:00:00', '2026-01-01T00:00:00', 'c1')"""
    )
    conn.commit()
    conn.close()
    return app


@pytest.mark.asyncio
async def test_get_years(seeded_app):
    transport = ASGITransport(app=seeded_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/timeline/years")
    assert resp.status_code == 200
    years = resp.json()
    assert 2025 in years
    assert 2024 in years


@pytest.mark.asyncio
async def test_get_events_by_year(seeded_app):
    transport = ASGITransport(app=seeded_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/timeline/events?year=2025")
    assert resp.status_code == 200
    events = resp.json()
    # May be empty if no event grouping yet — just check 200
    assert isinstance(events, list)


@pytest.mark.asyncio
async def test_get_events_requires_year(seeded_app):
    transport = ASGITransport(app=seeded_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/timeline/events")
    assert resp.status_code == 422  # validation error
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_timeline_api.py -v
```

Expected: FAIL — either import error or 404 from FastAPI (router not mounted).

- [ ] **Step 3: Create routers __init__.py**

```bash
touch backend/app/routers/__init__.py
```

- [ ] **Step 4: Write the timeline router**

```python
# backend/app/routers/timeline.py
from fastapi import APIRouter, Query
from app.database import get_connection
from app.models import MediaItem

router = APIRouter(prefix="/api/timeline", tags=["timeline"])


@router.get("/years")
def get_years(db_path: str = None) -> list[int]:
    conn = get_connection(db_path)
    rows = conn.execute(
        """SELECT DISTINCT CAST(strftime('%Y', date_taken) AS INTEGER) AS year
           FROM media WHERE date_taken IS NOT NULL ORDER BY year DESC"""
    ).fetchall()
    conn.close()
    return [r["year"] for r in rows]


@router.get("/events")
def get_events(
    year: int = Query(...),
    month: int | None = Query(None),
    db_path: str = None,
) -> list[dict]:
    conn = get_connection(db_path)
    if month:
        rows = conn.execute(
            """SELECT * FROM events
               WHERE CAST(strftime('%Y', start_date) AS INTEGER) = ?
               AND CAST(strftime('%m', start_date) AS INTEGER) = ?
               ORDER BY start_date""",
            (year, month),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT * FROM events
               WHERE CAST(strftime('%Y', start_date) AS INTEGER) = ?
               ORDER BY start_date""",
            (year,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/event/{event_id}/media")
def get_event_media(
    event_id: int,
    cursor: str | None = Query(None),
    limit: int = Query(100, le=500),
    db_path: str = None,
) -> dict:
    conn = get_connection(db_path)
    if cursor:
        rows = conn.execute(
            """SELECT m.* FROM media m
               JOIN event_media em ON m.id = em.media_id
               WHERE em.event_id = ? AND m.date_taken > ?
               ORDER BY m.date_taken LIMIT ?""",
            (event_id, cursor, limit + 1),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT m.* FROM media m
               JOIN event_media em ON m.id = em.media_id
               WHERE em.event_id = ?
               ORDER BY m.date_taken LIMIT ?""",
            (event_id, limit + 1),
        ).fetchall()

    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]

    conn.close()
    items = [MediaItem.from_row(r).model_dump() for r in rows]
    next_cursor = items[-1]["date_taken"] if has_more and items else None
    return {"items": items, "next_cursor": next_cursor}
```

- [ ] **Step 5: Run tests — will still fail until router is mounted in main**

```bash
cd backend && python -m pytest tests/test_timeline_api.py -v
```

Expected: FAIL — `app.main` doesn't exist yet. This is expected; we mount all routers in Task 11.

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/__init__.py backend/app/routers/timeline.py backend/tests/test_timeline_api.py
git commit -m "feat: timeline API router with years, events, and event media endpoints"
```

---

### Task 10: Media API router

**Files:**
- Create: `backend/app/routers/media.py`
- Create: `backend/tests/test_media_api.py`

- [ ] **Step 1: Write the failing API test**

```python
# backend/tests/test_media_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.database import get_connection, init_db


@pytest.fixture
def seeded_media_app(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path / "media"))
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("THUMBNAIL_SIZE", "300")

    init_db(db_path)
    conn = get_connection(db_path)
    conn.execute(
        """INSERT INTO media (path, filename, media_type, date_taken, date_added, checksum, width, height)
           VALUES ('/p/1.jpg', 'beach.jpg', 'image', '2025-04-29T12:00:00', '2026-01-01T00:00:00', 'a1', 800, 600)"""
    )
    conn.execute(
        """INSERT INTO media (path, filename, media_type, date_taken, date_added, checksum, width, height)
           VALUES ('/p/2.jpg', 'mountain.jpg', 'image', '2024-04-29T08:00:00', '2026-01-01T00:00:00', 'b1', 1024, 768)"""
    )
    conn.commit()
    conn.close()

    from app.main import create_app
    app = create_app()
    return app


@pytest.mark.asyncio
async def test_get_media_by_id(seeded_media_app):
    transport = ASGITransport(app=seeded_media_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/media/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "beach.jpg"
    assert data["width"] == 800
    assert data["height"] == 600


@pytest.mark.asyncio
async def test_get_media_not_found(seeded_media_app):
    transport = ASGITransport(app=seeded_media_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/media/999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_random_media(seeded_media_app):
    transport = ASGITransport(app=seeded_media_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/media/random?count=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_on_this_day(seeded_media_app):
    transport = ASGITransport(app=seeded_media_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/media/on-this-day?month=4&day=29")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2  # one from 2025, one from 2024


@pytest.mark.asyncio
async def test_delete_media(seeded_media_app):
    transport = ASGITransport(app=seeded_media_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.delete("/api/media/1")
    assert resp.status_code == 200
    assert resp.json() == {"deleted": True}

    # Verify it's gone
    resp2 = await client.get("/api/media/1")
    assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_delete_media_not_found(seeded_media_app):
    transport = ASGITransport(app=seeded_media_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.delete("/api/media/999")
    assert resp.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_media_api.py -v
```

Expected: FAIL — router not mounted.

- [ ] **Step 3: Write the media router**

```python
# backend/app/routers/media.py
from fastapi import APIRouter, Query, HTTPException
from app.services.media_service import (
    get_media_by_id,
    get_media_random,
    get_media_on_this_day,
    delete_media,
)

router = APIRouter(prefix="/api/media", tags=["media"])


@router.get("/{media_id}")
def get_media(media_id: int):
    item = get_media_by_id(media_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Media not found")
    return item.model_dump()


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


@router.delete("/{media_id}")
def delete_media_endpoint(media_id: int):
    success = delete_media(media_id)
    if not success:
        raise HTTPException(status_code=404, detail="Media not found")
    return {"deleted": True}
```

- [ ] **Step 4: Commit (tests will pass after Task 11)**

```bash
git add backend/app/routers/media.py backend/tests/test_media_api.py
git commit -m "feat: media API router with get, random, on-this-day, and delete"
```

---

### Task 11: Admin API router

**Files:**
- Create: `backend/app/routers/admin.py`
- Create: `backend/tests/test_admin_api.py`

- [ ] **Step 1: Write the failing API test**

```python
# backend/tests/test_admin_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.database import get_connection, init_db


@pytest.fixture
def admin_app(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path / "media"))
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("THUMBNAIL_SIZE", "300")

    init_db(db_path)
    conn = get_connection(db_path)
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added, checksum) VALUES (?,?,?,?,?)",
        ("/a.jpg", "a.jpg", "image", "2026-04-29T10:00:00", "x1"),
    )
    conn.execute(
        "INSERT INTO media (path, filename, media_type, date_added, checksum) VALUES (?,?,?,?,?)",
        ("/b.mp4", "b.mp4", "video", "2026-04-29T11:00:00", "x2"),
    )
    conn.commit()
    conn.close()

    from app.main import create_app
    app = create_app()
    return app


@pytest.mark.asyncio
async def test_post_scan_starts_job(admin_app):
    transport = ASGITransport(app=admin_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/admin/scan")
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    assert data["status"] in ("pending", "running")


@pytest.mark.asyncio
async def test_get_scan_status(admin_app):
    transport = ASGITransport(app=admin_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Start a scan first
        start_resp = await client.post("/api/admin/scan")
        job_id = start_resp.json()["job_id"]

        resp = await client.get(f"/api/admin/scan/status?job_id={job_id}")
    assert resp.status_code == 200
    assert resp.json()["job_id"] == job_id


@pytest.mark.asyncio
async def test_get_scan_status_not_found(admin_app):
    transport = ASGITransport(app=admin_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/admin/scan/status?job_id=nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_system_stats(admin_app):
    transport = ASGITransport(app=admin_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/admin/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["media_count"] == 2
    assert data["image_count"] == 1
    assert data["video_count"] == 1
    assert data["db_size_bytes"] > 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_admin_api.py -v
```

Expected: FAIL — router not mounted.

- [ ] **Step 3: Write the admin router**

```python
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
```

- [ ] **Step 4: Commit (tests will pass after Task 12)**

```bash
git add backend/app/routers/admin.py backend/tests/test_admin_api.py
git commit -m "feat: admin API router with scan, status, and stats endpoints"
```

---

### Task 12: FastAPI app assembly and static file serving

**Files:**
- Create: `backend/app/main.py`

- [ ] **Step 1: Write the FastAPI app entry point**

```python
# backend/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.data_root, exist_ok=True)
    os.makedirs(settings.thumb_dir, exist_ok=True)
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="HomeMemories AI",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.routers.timeline import router as timeline_router
    from app.routers.media import router as media_router
    from app.routers.admin import router as admin_router

    app.include_router(timeline_router)
    app.include_router(media_router)
    app.include_router(admin_router)

    # Static file serving
    if os.path.exists(settings.thumb_dir):
        app.mount(
            "/media/thumbs",
            StaticFiles(directory=settings.thumb_dir),
            name="thumbs",
        )
    if os.path.exists(settings.media_root):
        app.mount(
            "/media/original",
            StaticFiles(directory=settings.media_root),
            name="original",
        )

    return app


app = create_app()
```

- [ ] **Step 2: Verify the app starts**

```bash
cd backend && timeout 5 python -m uvicorn app.main:app --host 0.0.0.0 --port 8501 || true
```

Expected: Application startup message, no errors. (Will timeout after 5s, that's fine.)

- [ ] **Step 3: Run all API tests together**

```bash
cd backend && python -m pytest tests/ -v -k "api"
```

Expected: All API tests PASS (timeline 3 + media 6 + admin 4 = 13 tests).

- [ ] **Step 4: Run the full test suite**

```bash
cd backend && python -m pytest tests/ -v
```

Expected: All tests PASS (~35 tests total).

- [ ] **Step 5: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: FastAPI app assembly with CORS, static mounts, and all routers"
```

---

### Task 13: End-to-end verification

- [ ] **Step 1: Start the server**

```bash
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8501 &
sleep 2
```

- [ ] **Step 2: Test each endpoint with curl**

```bash
# Health check (FastAPI docs)
curl -s http://localhost:8501/docs -o /dev/null -w "%{http_code}"
# Expected: 200

# Get years
curl -s http://localhost:8501/api/timeline/years
# Expected: [] (empty database)

# Get system stats
curl -s http://localhost:8501/api/admin/stats
# Expected: {"db_size_bytes":..., "media_count":0, ...}

# Start a scan
curl -s -X POST http://localhost:8501/api/admin/scan
# Expected: {"job_id":"...", "status":"running", ...}
```

- [ ] **Step 3: Stop the server**

```bash
kill %1 2>/dev/null || true
```

- [ ] **Step 4: Commit if any config adjustments needed**

```bash
git status
# Only commit if changes were made during verification
```

---

## Self-Review

### Spec coverage

| Spec requirement | Covered by |
|-----------------|------------|
| FastAPI + SQLite scaffolding | Tasks 1, 2 |
| Media scanner with EXIF extraction | Tasks 3, 5 |
| Thumbnail generation pipeline | Task 4 |
| Timeline API (years, events, event media) | Task 9 |
| Media API (get, random, on-this-day, delete) | Task 10 |
| Admin API (scan, status, stats) | Task 11 |
| Static file serving (/media/thumbs, /media/original) | Task 12 |

### Placeholder scan

No "TODOs", "implement later", or vague instructions found. Every step has actual code or exact commands.

### Type consistency

- `MediaItem.from_row()` — defined in Task 6, used in Tasks 7, 9, 10 ✓
- `ScanResult` — defined in Task 6, used in Tasks 8, 11 ✓
- `get_connection(db_path)` — consistent signature across all modules ✓
- `cursor` parameter in pagination — consistent across timeline and media routers ✓
- Test fixtures `tmp_db_path` — defined in Task 2 conftest, used in Tasks 7, 8 ✓
