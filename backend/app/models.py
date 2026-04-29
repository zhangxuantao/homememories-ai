# backend/app/models.py
from pydantic import BaseModel


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
