// ── Types matching backend Pydantic models ──

export interface MediaItem {
  id: number;
  path: string;
  filename: string;
  media_type: 'image' | 'video';
  width: number | null;
  height: number | null;
  file_size: number | null;
  date_taken: string | null;
  date_added: string;
  thumbnail_path: string | null;
  duration: number | null;
  is_blurry: boolean;
}

export interface TimelineEvent {
  id: number;
  title: string;
  start_date: string;
  end_date: string;
  cover_media_id: number | null;
  media_count: number;
  location: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  next_cursor: string | null;
}

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  error: string | null;
}

export interface ScanStatus {
  job_id: string;
  status: string;
  progress: number;
  total: number;
  new: number;
  skipped: number;
  error: string | null;
}

export interface SystemStats {
  db_size_bytes: number;
  media_count: number;
  image_count: number;
  video_count: number;
  last_scan_time: string | null;
}

export interface SearchResponse {
  results: MediaItem[];
  next_cursor: string | null;
}

export interface FaceCluster {
  id: number;
  label: string | null;
  cover_face_id: number | null;
  photo_count: number;
  cover_thumbnail: string | null;
}

// ── API Client ──

const BASE_URL = '';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private buildUrl(path: string, params?: Record<string, string | number | undefined>): string {
    const base = this.baseUrl || window.location.origin;
    const url = new URL(path, base);
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
      });
    }
    return url.toString();
  }

  async get<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
    const res = await fetch(this.buildUrl(path, params));
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`${res.status} ${res.statusText}: ${text}`);
    }
    return res.json();
  }

  async post<T>(path: string, body?: unknown, params?: Record<string, string | undefined>): Promise<T> {
    const res = await fetch(this.buildUrl(path, params), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`${res.status} ${res.statusText}: ${text}`);
    }
    return res.json();
  }

  async upload<T>(path: string, file: File): Promise<T> {
    const formData = new FormData();
    formData.append('image_file', file);
    const res = await fetch(this.buildUrl(path), {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`${res.status} ${res.statusText}: ${text}`);
    }
    return res.json();
  }

  async delete<T>(path: string, body?: unknown): Promise<T> {
    const res = await fetch(this.buildUrl(path), {
      method: 'DELETE',
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`${res.status} ${res.statusText}: ${text}`);
    }
    return res.json();
  }

  async patch<T>(path: string, body?: unknown, params?: Record<string, string | undefined>): Promise<T> {
    const res = await fetch(this.buildUrl(path, params), {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`${res.status} ${res.statusText}: ${text}`);
    }
    return res.json();
  }

  thumbUrl(thumbnailPath: string | null | undefined): string {
    if (!thumbnailPath) return '';
    const base = this.baseUrl || '';
    return `${base}/media/thumbs/${thumbnailPath}`;
  }

  faceThumbUrl(thumbnailPath: string | null | undefined): string {
    if (!thumbnailPath) return '';
    const base = this.baseUrl || '';
    return `${base}/media/faces/${thumbnailPath}`;
  }

  originalUrl(mediaId: number, _path?: string): string {
    const base = this.baseUrl || '';
    return `${base}/api/media/${mediaId}/file`;
  }
}

export const api = new ApiClient(BASE_URL);
