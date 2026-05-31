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

export interface Album {
  id: number;
  name: string;
  cover_media_id: number | null;
  cover_thumbnail: string | null;
  media_count: number;
  created_at: string;
  updated_at: string;
}

export interface GpuInfo {
  cuda_available: boolean;
  device_name: string | null;
  device_count: number;
  memory_total_gb: number | null;
  memory_used_gb: number | null;
}

export interface ModelInfo {
  clip_loaded: boolean;
  clip_device: string;
}

export interface ServerInfo {
  hostname: string;
  lan_ip: string;
  port: number;
  frontend_port: number;
  gpu: GpuInfo;
  models: ModelInfo;
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

  async uploadFormData<T>(path: string, formData: FormData): Promise<T> {
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

  async getServerInfo(): Promise<ServerInfo> {
    return this.get<ServerInfo>('/api/admin/server-info');
  }

  async toggleFavorite(mediaId: number): Promise<{ favorited: boolean }> {
    return this.post<{ favorited: boolean }>(`/api/favorites/${mediaId}`);
  }

  async getFavorites(limit?: number, offset?: number): Promise<MediaItem[]> {
    return this.get<MediaItem[]>('/api/favorites', { limit, offset });
  }

  async getRecentFavorites(limit?: number): Promise<MediaItem[]> {
    return this.get<MediaItem[]>('/api/favorites/recent', { limit });
  }

  async checkFavorites(ids: number[]): Promise<Record<string, boolean>> {
    if (ids.length === 0) return {};
    return this.get<Record<string, boolean>>(`/api/favorites/check?ids=${ids.join(',')}`);
  }

  async deleteDuplicateMedia(keepId: number, deleteIds: number[]): Promise<{ deleted: number }> {
    return this.delete<{ deleted: number }>('/api/admin/cleanup/duplicates', { keep_id: keepId, delete_ids: deleteIds });
  }

  // ── Albums ──

  async listAlbums(): Promise<Album[]> {
    return this.get<Album[]>('/api/albums');
  }

  async createAlbum(name: string): Promise<Album> {
    return this.post<Album>('/api/albums', { name });
  }

  async getAlbum(id: number): Promise<Album> {
    return this.get<Album>(`/api/albums/${id}`);
  }

  async updateAlbum(id: number, data: { name?: string; cover_media_id?: number }): Promise<Album> {
    return this.patch<Album>(`/api/albums/${id}`, data);
  }

  async deleteAlbum(id: number): Promise<{ deleted: number }> {
    return this.delete<{ deleted: number }>(`/api/albums/${id}`);
  }

  async getAlbumMedia(id: number, limit?: number): Promise<MediaItem[]> {
    return this.get<{ items: MediaItem[] }>(`/api/albums/${id}/media`, { limit })
      .then(r => r.items);
  }

  async addToAlbum(albumId: number, mediaIds: number[]): Promise<{ added: number }> {
    return this.post<{ added: number }>(`/api/albums/${albumId}/media`, { media_ids: mediaIds });
  }

  async removeFromAlbum(albumId: number, mediaIds: number[]): Promise<{ deleted: number }> {
    return this.delete<{ deleted: number }>(`/api/albums/${albumId}/media`, mediaIds);
  }
}

export const api = new ApiClient(BASE_URL);
