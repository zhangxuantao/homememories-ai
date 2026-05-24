# P1 Group A: 重复删除 + 收藏 + GPU 状态 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement duplicate photo deletion UX, global favorites feature, and GPU status display on the Settings page.

**Architecture:** Three independent features implemented across backend (DB schema changes, 4 API endpoints, 1 extended endpoint) and frontend (2 new files, 5 modified files). Backend-first, then frontend. Favorites uses a standalone SQLite table with toggle-based POST API; duplicates adds a DELETE endpoint reusing existing `delete_media`; GPU info extends the existing `server-info` endpoint.

**Tech Stack:** FastAPI + SQLite, React 18 + TypeScript + Tailwind CSS 3

---

## File Change Summary

| Operation | File | Purpose |
|-----------|------|---------|
| Modify | `backend/app/database.py` | Add `favorites` table to SCHEMA |
| Modify | `backend/app/routers/admin.py` | Add `DELETE /cleanup/duplicates` endpoint; extend `server-info` with GPU + models fields |
| Create | `backend/app/routers/favorites.py` | Full favorites CRUD router |
| Modify | `backend/app/main.py` | Register favorites router |
| Create | `backend/tests/test_duplicates_api.py` | Tests for duplicate delete endpoint |
| Create | `backend/tests/test_favorites_api.py` | Tests for favorites endpoints |
| Modify | `frontend/src/api/client.ts` | Add GpuInfo, ModelInfo, ServerInfo extension, favorites API methods |
| Create | `frontend/src/hooks/useFavorites.ts` | SWR-style hooks for favorites data |
| Modify | `frontend/src/components/gallery/Lightbox.tsx` | Add ♡/♥ favorite button to top bar |
| Create | `frontend/src/pages/FavoritesPage.tsx` | Full favorites page with grid, empty state, batch unfavorite |
| Modify | `frontend/src/pages/HomePage.tsx` | Add "最近收藏" horizontal scroll section |
| Modify | `frontend/src/pages/SettingsPage.tsx` | Duplicate pair delete UI + GPU info card |
| Modify | `frontend/src/components/layout/MobileNav.tsx` | Expand TABS from 5→6 items |
| Modify | `frontend/src/components/layout/DesktopRail.tsx` | Expand TABS from 5→6 items |
| Modify | `frontend/src/App.tsx` | Add `/favorites` route |

---

### Task 1: Database — Add favorites table

**Files:**
- Modify: `backend/app/database.py:86` (after album_media table, before indexes)

- [ ] **Step 1: Add favorites table to SCHEMA**

Add the following after the `album_media` CREATE TABLE block (line 97) and before the index section (line 99):

```sql
CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id INTEGER NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE
);
```

Also add the index after line 107:

```sql
CREATE INDEX IF NOT EXISTS idx_favorites_created ON favorites(created_at DESC);
```

- [ ] **Step 2: Restart backend to apply schema**

Run: `curl -s http://localhost:8501/api/admin/stats | head -20`
Expected: Backend starts without error, `init_db()` applies new table.

- [ ] **Step 3: Verify table exists**

Run: `sqlite3 backend/data/metadata.db ".schema favorites"`
Expected: Shows CREATE TABLE output for favorites table.

- [ ] **Step 4: Commit**

```bash
git add backend/app/database.py
git commit -m "feat: 新增 favorites 收藏表"
```

---

### Task 2: Backend — DELETE /api/admin/cleanup/duplicates endpoint

**Files:**
- Modify: `backend/app/routers/admin.py:88`
- Create: `backend/tests/test_duplicates_api.py`

- [ ] **Step 1: Add DeleteDuplicatesRequest model and endpoint**

Add after the `delete_blurry_media` function (line 94) in `admin.py`:

First add the import at line 3 (Pydantic BaseModel is already imported, verify):

```python
from pydantic import BaseModel
```

Already imported at line 2 of albums.py — check admin.py. If not, add it. Then add after line 94:

```python
class DeleteDuplicatesRequest(BaseModel):
    keep_id: int
    delete_ids: list[int]


@router.delete("/cleanup/duplicates")
def delete_duplicate_media(body: DeleteDuplicatesRequest):
    deleted = 0
    for mid in body.delete_ids:
        try:
            delete_media(mid)
            deleted += 1
        except Exception:
            pass
    return {"deleted": deleted}
```

Check imports: `delete_media` is already imported at line 19. If `BaseModel` is not imported, add it to `from pydantic` line or import separately.

- [ ] **Step 2: Add test file**

Create `backend/tests/test_duplicates_api.py`:

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_delete_duplicates_basic():
    """Delete duplicate media should succeed with valid IDs."""
    payload = {"keep_id": 1, "delete_ids": [2, 3]}
    resp = client.delete("/api/admin/cleanup/duplicates", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "deleted" in data
    assert isinstance(data["deleted"], int)


def test_delete_duplicates_empty_list():
    """Deleting an empty list should return deleted=0."""
    resp = client.delete("/api/admin/cleanup/duplicates", json={"keep_id": 1, "delete_ids": []})
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 0


def test_delete_duplicates_missing_keep():
    """Request missing keep_id should get 422 validation error."""
    resp = client.delete("/api/admin/cleanup/duplicates", json={"delete_ids": [2]})
    assert resp.status_code == 422
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_duplicates_api.py -v`
Expected: 3/3 tests pass.

- [ ] **Step 4: Commit**

```bash
git add backend/app/routers/admin.py backend/tests/test_duplicates_api.py
git commit -m "feat: 新增 DELETE /api/admin/cleanup/duplicates 重复删除端点"
```

---

### Task 3: Backend — Favorites router (CRUD endpoints)

**Files:**
- Create: `backend/app/routers/favorites.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_favorites_api.py`

- [ ] **Step 1: Create favorites router**

Create `backend/app/routers/favorites.py`:

```python
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timezone

from app.database import get_connection

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.post("/{media_id}")
def toggle_favorite(media_id: int):
    conn = get_connection()
    existing = conn.execute(
        "SELECT id FROM favorites WHERE media_id = ?", (media_id,)
    ).fetchone()

    if existing:
        conn.execute("DELETE FROM favorites WHERE id = ?", (existing["id"],))
        conn.commit()
        conn.close()
        return {"favorited": False}
    else:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO favorites (media_id, created_at) VALUES (?, ?)",
            (media_id, now),
        )
        conn.commit()
        conn.close()
        return {"favorited": True}


@router.get("")
def list_favorites(limit: int = 50, offset: int = 0):
    conn = get_connection()
    rows = conn.execute(
        """SELECT m.*, f.created_at as fav_created_at
           FROM favorites f
           JOIN media m ON f.media_id = m.id
           ORDER BY f.created_at DESC
           LIMIT ? OFFSET ?""",
        (limit, offset),
    ).fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "path": r["path"],
            "filename": r["filename"],
            "media_type": r["media_type"],
            "width": r["width"],
            "height": r["height"],
            "file_size": r["file_size"],
            "date_taken": r["date_taken"],
            "date_added": r["date_added"],
            "thumbnail_path": r["thumbnail_path"],
            "duration": r["duration"],
            "is_blurry": bool(r["is_blurry"]),
            "fav_created_at": r["fav_created_at"],
        }
        for r in rows
    ]


@router.get("/recent")
def recent_favorites(limit: int = 6):
    return list_favorites(limit=limit, offset=0)


@router.get("/check")
def check_favorites(ids: str = Query("")):
    if not ids:
        return {}
    try:
        id_list = [int(x.strip()) for x in ids.split(",") if x.strip()]
    except ValueError:
        return {}
    if not id_list:
        return {}

    conn = get_connection()
    placeholders = ",".join("?" * len(id_list))
    rows = conn.execute(
        f"SELECT media_id FROM favorites WHERE media_id IN ({placeholders})",
        id_list,
    ).fetchall()
    conn.close()

    fav_set = {r["media_id"] for r in rows}
    return {str(mid): mid in fav_set for mid in id_list}
```

- [ ] **Step 2: Register favorites router in main.py**

In `backend/app/main.py`, find the line where routers are registered (search for `app.include_router`). Add after the last `include_router` line:

```python
from app.routers import favorites
app.include_router(favorites.router)
```

- [ ] **Step 3: Create tests**

Create `backend/tests/test_favorites_api.py`:

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_toggle_favorite_add_then_remove():
    """POST toggle should add favorite then remove it."""
    # Add favorite
    resp = client.post("/api/favorites/1")
    assert resp.status_code == 200
    assert resp.json()["favorited"] is True

    # Toggle again to remove
    resp = client.post("/api/favorites/1")
    assert resp.status_code == 200
    assert resp.json()["favorited"] is False


def test_list_favorites():
    """GET favorites should return list of MediaItem objects."""
    # Ensure at least one favorite exists
    client.post("/api/favorites/1")
    resp = client.get("/api/favorites")
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list)
    if len(items) > 0:
        item = items[0]
        assert "id" in item
        assert "filename" in item
        assert "fav_created_at" in item


def test_check_favorites():
    """GET check should return dict of media_id -> boolean."""
    client.post("/api/favorites/1")
    resp = client.get("/api/favorites/check?ids=1,2,999")
    assert resp.status_code == 200
    data = resp.json()
    assert data["1"] is True
    assert data["2"] is False
    assert data["999"] is False


def test_recent_favorites():
    """GET recent should return at most limit items."""
    resp = client.get("/api/favorites/recent?limit=3")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) <= 3
```

- [ ] **Step 4: Run tests**

Run: `cd backend && python -m pytest tests/test_favorites_api.py -v`
Expected: 4/4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/favorites.py backend/app/main.py backend/tests/test_favorites_api.py
git commit -m "feat: 新增收藏功能 API — toggle/list/recent/check 四个端点"
```

---

### Task 4: Backend — Extend server-info with GPU + model status

**Files:**
- Modify: `backend/app/routers/admin.py:126-142` (server_info function)

- [ ] **Step 1: Add GPU and model info to server-info endpoint**

Replace the `server_info` function in `admin.py` (lines 126-142) with:

```python
@router.get("/server-info")
def server_info():
    hostname = socket.gethostname()
    lan_ip = ""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        lan_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    # GPU info — fail gracefully
    gpu = {"cuda_available": False, "device_name": None, "device_count": 0,
           "memory_total_gb": None, "memory_used_gb": None}
    try:
        import torch
        gpu["cuda_available"] = torch.cuda.is_available()
        if gpu["cuda_available"]:
            gpu["device_name"] = torch.cuda.get_device_name(0)
            gpu["device_count"] = torch.cuda.device_count()
            gpu["memory_total_gb"] = round(
                torch.cuda.get_device_properties(0).total_memory / 1e9, 1
            )
            gpu["memory_used_gb"] = round(
                torch.cuda.memory_allocated(0) / 1e9, 2
            )
    except Exception:
        pass

    # Model status
    models = {"clip_loaded": False, "clip_device": "not_loaded"}
    try:
        from app.ai.embedding import EmbeddingPipeline
        inst = EmbeddingPipeline()
        if inst._initialized:
            models["clip_loaded"] = True
            models["clip_device"] = str(inst.device)
    except Exception:
        pass

    return {
        "hostname": hostname,
        "lan_ip": lan_ip,
        "port": 8501,
        "frontend_port": 5173,
        "gpu": gpu,
        "models": models,
    }
```

- [ ] **Step 2: Verify endpoint works**

Run: `curl -s http://localhost:8501/api/admin/server-info | python -m json.tool`
Expected: Response includes `gpu` and `models` sub-objects with correct fields.

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/admin.py
git commit -m "feat: server-info 端点扩展 GPU 状态和模型加载信息"
```

---

### Task 5: Frontend — API Client + useFavorites hook

**Files:**
- Modify: `frontend/src/api/client.ts`
- Create: `frontend/src/hooks/useFavorites.ts`

- [ ] **Step 1: Add TypeScript interfaces and API methods to client.ts**

After the `ServerInfo` interface (line 76), add:

```typescript
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

// Update ServerInfo interface (replace lines 71-76):
```

Actually replace the existing `ServerInfo` interface (lines 71-76):

```typescript
export interface ServerInfo {
  hostname: string;
  lan_ip: string;
  port: number;
  frontend_port: number;
  gpu: GpuInfo;
  models: ModelInfo;
}
```

At the end of the `ApiClient` class (before the closing `}`), add favorites methods:

```typescript
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
```

Also add `deleteDuplicateMedia` method:

```typescript
  async deleteDuplicateMedia(keepId: number, deleteIds: number[]): Promise<{ deleted: number }> {
    return this.delete<{ deleted: number }>('/api/admin/cleanup/duplicates', { keep_id: keepId, delete_ids: deleteIds });
  }
```

- [ ] **Step 2: Create useFavorites hook**

Create `frontend/src/hooks/useFavorites.ts`:

```typescript
import { useState, useEffect, useCallback } from 'react';
import { api, MediaItem } from '../api/client';

export function useFavorites(limit: number = 50) {
  const [items, setItems] = useState<MediaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [offset, setOffset] = useState(0);

  const fetch = useCallback(async (reset = false) => {
    setLoading(true);
    const o = reset ? 0 : offset;
    try {
      const data = await api.getFavorites(limit, o);
      setItems(prev => reset ? data : [...prev, ...data]);
      if (reset) setOffset(limit);
      else setOffset(o + limit);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [limit, offset]);

  useEffect(() => { fetch(true); }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  const loadMore = useCallback(() => fetch(false), [fetch]);
  const refresh = useCallback(() => fetch(true), [fetch]);

  const toggleFavorite = useCallback(async (mediaId: number) => {
    const res = await api.toggleFavorite(mediaId);
    if (!res.favorited) {
      setItems(prev => prev.filter(item => item.id !== mediaId));
    } else {
      refresh();
    }
    return res.favorited;
  }, [refresh]);

  return { items, loading, loadMore, toggleFavorite, refresh };
}

export function useRecentFavorites(limit: number = 6) {
  const [items, setItems] = useState<MediaItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getRecentFavorites(limit);
      setItems(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => { fetch(); }, [fetch]);

  return { items, loading, refresh: fetch };
}

export function useFavoriteStatus(mediaId: number | null) {
  const [favorited, setFavorited] = useState(false);

  useEffect(() => {
    if (mediaId === null) return;
    api.checkFavorites([mediaId]).then(data => {
      setFavorited(data[String(mediaId)] ?? false);
    }).catch(() => {});
  }, [mediaId]);

  const toggle = useCallback(async () => {
    if (mediaId === null) return;
    const res = await api.toggleFavorite(mediaId);
    setFavorited(res.favorited);
  }, [mediaId]);

  return { favorited, toggle };
}
```

- [ ] **Step 3: Verify TypeScript compilation**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -20`
Expected: No new type errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/api/client.ts frontend/src/hooks/useFavorites.ts
git commit -m "feat: 前端 API client 扩展 — favorites 方法 + useFavorites hooks + ServerInfo GPU 类型"
```

---

### Task 6: Frontend — Lightbox favorite button

**Files:**
- Modify: `frontend/src/components/gallery/Lightbox.tsx`

- [ ] **Step 1: Add favorite button to Lightbox top bar**

Add import at top:
```typescript
import { useState, useCallback, useEffect } from 'react';  // already has these
import { useFavoriteStatus } from '../../hooks/useFavorites';
```

In the component body, add after `loadingSimilar` state (line 19):
```typescript
const { favorited, toggle: toggleFav } = useFavoriteStatus(item.id);
```

Replace the top bar actions div (lines 81-96) to insert favorite button between similar and download:

```tsx
<div className="flex items-center gap-4">
  <button
    onClick={handleShowSimilar}
    className={`hover:text-primary transition-colors ${showSimilar ? 'text-primary' : ''}`}
  >
    {showSimilar ? '隐藏相似' : '相似照片'}
  </button>
  <button
    onClick={(e) => { e.stopPropagation(); toggleFav(); }}
    className={`transition-colors text-lg ${favorited ? 'text-[#f67280]' : 'text-white/60 hover:text-white'}`}
    title={favorited ? '取消收藏' : '收藏'}
  >
    {favorited ? '♥' : '♡'}
  </button>
  <a
    href={displayUrl}
    download={item.filename}
    className="hover:text-primary transition-colors"
    onClick={(e) => e.stopPropagation()}
  >
    下载
  </a>
</div>
```

- [ ] **Step 2: Verify in browser**

Instructions: Open a photo in the app (e.g. http://localhost:5173/photo/1). Verify:
- Heart icon shows ♡ (outline) before clicking
- Clicking toggles to ♥ (filled, pink `#f67280`)
- Clicking again toggles back
- Clicking does not close the lightbox (`stopPropagation`)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/gallery/Lightbox.tsx
git commit -m "feat: Lightbox 顶栏新增收藏按钮 — ♡/♥ 乐观切换"
```

---

### Task 7: Frontend — MobileNav + DesktopRail 6 tabs + FavoritesPage + routing

**Files:**
- Modify: `frontend/src/components/layout/MobileNav.tsx`
- Modify: `frontend/src/components/layout/DesktopRail.tsx`
- Create: `frontend/src/pages/FavoritesPage.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Update DesktopRail TABS array**

In `DesktopRail.tsx`, replace the TABS constant:

```typescript
const TABS = [
  { to: '/', label: '首页', icon: '🏠' },
  { to: '/timeline', label: '时间线', icon: '📅' },
  { to: '/favorites', label: '收藏', icon: '❤️' },
  { to: '/search', label: '搜索', icon: '🔍' },
  { to: '/people', label: '人物', icon: '👤' },
  { to: '/settings', label: '设置', icon: '⚙️' },
];
```

- [ ] **Step 2: Update MobileNav TABS array**

In `MobileNav.tsx`, replace the TABS constant:

```typescript
const TABS = [
  { to: '/', label: '首页', icon: '🏠' },
  { to: '/timeline', label: '时间线', icon: '📅' },
  { to: '/favorites', label: '收藏', icon: '❤️' },
  { to: '/search', label: '搜索', icon: '🔍' },
  { to: '/people', label: '人物', icon: '👤' },
  { to: '/settings', label: '设置', icon: '⚙️' },
];
```

The `grid-cols-5` class on the nav element needs to become `grid-cols-6`:

```tsx
<nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 grid grid-cols-6 items-end h-14 bg-white/90 backdrop-blur-xl border-t border-misty pb-1">
```

- [ ] **Step 3: Create FavoritesPage**

Create `frontend/src/pages/FavoritesPage.tsx`:

```tsx
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useFavorites } from '../hooks/useFavorites';
import { useSelection } from '../hooks/useSelection';
import PhotoGrid from '../components/gallery/PhotoGrid';
import SelectionBar from '../components/gallery/SelectionBar';
import { api } from '../api/client';

export default function FavoritesPage() {
  const navigate = useNavigate();
  const { items, loading, loadMore, toggleFavorite } = useFavorites();
  const selection = useSelection();

  const handleItemClick = (id: number) => {
    navigate(`/photo/${id}`, { state: { from: '/favorites' } });
  };

  const handleBatchUnfavorite = async () => {
    const ids = Array.from(selection.selectedIds);
    if (!confirm(`确定取消收藏这 ${ids.length} 张照片？`)) return;
    for (const id of ids) {
      try {
        await api.toggleFavorite(id);
      } catch {}
    }
    selection.exitSelectMode();
    window.location.reload();
  };

  const handleDelete = async () => {
    // Reuse batch unfavorite as "delete from favorites"
    await handleBatchUnfavorite();
  };

  if (loading && items.length === 0) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!loading && items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[80vh] px-6 text-center">
        <span className="text-6xl mb-4">❤️</span>
        <p className="text-lg text-text font-semibold mb-2">还没有收藏照片哦</p>
        <p className="text-sm text-text-light">在照片详情页点击 ♡ 即可收藏</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 md:py-8">
      <motion.h1
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-2xl font-bold text-text mb-6"
      >
        ❤️ 我的收藏
      </motion.h1>

      <SelectionBar selection={selection} />
      <PhotoGrid items={items} onItemClick={handleItemClick} selection={selection} />

      {selection.selectMode && (
        <div className="fixed bottom-0 left-0 right-0 z-[60] flex justify-center items-center py-3 px-4 bg-white/95 backdrop-blur-md border-t border-misty md:ml-14">
          <button
            onClick={handleDelete}
            className="flex flex-col items-center gap-1 text-sm text-text hover:text-red-500 transition-colors"
          >
            <span className="text-xl">💔</span>
            <span className="text-[10px]">取消收藏 ({selection.selectedIds.size})</span>
          </button>
        </div>
      )}

      {!loading && items.length >= 50 && (
        <div className="flex justify-center mt-6">
          <button
            onClick={loadMore}
            className="px-4 py-2 text-sm text-primary border border-primary rounded-btn hover:bg-primary hover:text-white transition-colors"
          >
            加载更多
          </button>
        </div>
      )}

      {loading && items.length > 0 && (
        <div className="flex justify-center py-6">
          <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Add route in App.tsx**

In `App.tsx`, add the lazy import (after the existing ones):

```typescript
const FavoritesPage = lazy(() => import('./pages/FavoritesPage'));
```

Add the route before the settings route:

```tsx
<Route path="/favorites" element={<AnimatedPage><FavoritesPage /></AnimatedPage>} />
```

- [ ] **Step 5: Verify TypeScript compilation**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -20`
Expected: No errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/layout/MobileNav.tsx frontend/src/components/layout/DesktopRail.tsx frontend/src/pages/FavoritesPage.tsx frontend/src/App.tsx
git commit -m "feat: 收藏独立页 — FavoritesPage + 两端导航 6 tab + /favorites 路由"
```

---

### Task 8: Frontend — HomePage "最近收藏" section

**Files:**
- Modify: `frontend/src/pages/HomePage.tsx`

- [ ] **Step 1: Add recent favorites to HomePage**

Add import at top:
```typescript
import { useRecentFavorites } from '../hooks/useFavorites';
```

In the component, add hook call after `randomSecond`:
```typescript
const { items: recentFavs } = useRecentFavorites(6);
```

Add `hasRecentFavs` variable:
```typescript
const hasRecentFavs = recentFavs.length > 0;
```

Insert the recent favorites section between "随机回忆" (lines 99-126) and "最近添加" (lines 129-153):

```tsx
{/* Section 2.5: 最近收藏 */}
{hasRecentFavs && (
  <section className="mb-8">
    <h2 className="text-base font-semibold text-text mb-3 flex justify-between items-center">
      <span>❤️ 最近收藏</span>
      <button
        onClick={() => navigate('/favorites')}
        className="text-xs text-primary font-normal hover:underline"
      >
        查看全部 →
      </button>
    </h2>
    <div className="flex gap-2 overflow-x-auto scrollbar-none pb-1">
      {recentFavs.map((item) => (
        <div
          key={item.id}
          className="flex-shrink-0 w-20 h-20 rounded-card overflow-hidden bg-misty cursor-pointer hover:opacity-80 transition-opacity"
          onClick={() => navigate(`/photo/${item.id}`, { state: { from: '/' } })}
        >
          {item.thumbnail_path ? (
            <img
              src={api.thumbUrl(item.thumbnail_path)}
              alt={item.filename}
              className="w-full h-full object-cover"
              loading="lazy"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-2xl">📷</div>
          )}
        </div>
      ))}
    </div>
  </section>
)}
```

- [ ] **Step 2: Verify TypeScript compilation**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -20`
Expected: No new errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/HomePage.tsx
git commit -m "feat: 首页新增最近收藏横向滚动 section — 最多6张 + 查看全部链接"
```

---

### Task 9: Frontend — SettingsPage: duplicate delete UI + GPU info

**Files:**
- Modify: `frontend/src/pages/SettingsPage.tsx`

- [ ] **Step 1: Add duplicate selection hook and delete handler**

After the existing `const blurrySelection = useSelection();` (line 84), add:
```typescript
const duplicateSelection = useSelection();
```

After `handleDeleteBlurry` function (line 141), add duplicate delete handler:

```typescript
const handleDuplicateBatchDelete = async () => {
  if (!duplicatePairs) return;
  const selectedIds = Array.from(duplicateSelection.selectedIds);
  if (selectedIds.length === 0) return;
  if (!confirm(`确定删除这 ${selectedIds.length} 张重复照片？此操作不可恢复。`)) return;

  // For each pair, figure out which are being deleted
  for (const pair of duplicatePairs) {
    const deleteIds = pair
      .map((m: MediaItem) => m.id)
      .filter((id: number) => selectedIds.includes(id));
    if (deleteIds.length > 0 && deleteIds.length < pair.length) {
      const keepId = pair.find((m: MediaItem) => !selectedIds.has(m.id))?.id;
      if (keepId) {
        try {
          await api.deleteDuplicateMedia(keepId, deleteIds);
        } catch {}
      }
    }
  }
  duplicateSelection.exitSelectMode();
  // Refresh duplicate pairs
  const fresh = await fetchDuplicatePairs();
  setDuplicatePairs(fresh);
};
```

- [ ] **Step 2: Replace duplicate results section (lines 296-314) with full selection-enabled version**

Replace the duplicate results display block (the `{showDuplicates && duplicatePairs !== null && (` block at lines 295-314) with:

```tsx
{showDuplicates && duplicatePairs !== null && (
  <div className="mt-3">
    <div className="flex items-center justify-between mb-2">
      <p className="text-sm text-text-light">
        {duplicatePairs.length === 0 ? '没有检测到重复照片' : `找到 ${duplicatePairs.length} 组重复照片`}
      </p>
      {duplicatePairs.length > 0 && !duplicateSelection.selectMode && (
        <button
          onClick={() => duplicateSelection.enterSelectMode()}
          className="text-xs text-primary border border-primary px-2 py-0.5 rounded-btn hover:bg-primary hover:text-white transition-colors"
        >
          批量选择
        </button>
      )}
    </div>

    <SelectionBar selection={duplicateSelection} />

    {duplicatePairs.length > 0 && (
      <div className="space-y-3">
        {duplicatePairs.map((pair, i) => {
          return (
            <div key={i} className="glass-card rounded-card p-2">
              <p className="text-xs text-text-light mb-1">重复组 {i + 1}</p>
              <div className="grid grid-cols-2 gap-2">
                {pair.map((item: MediaItem) => {
                  const isSel = duplicateSelection.isSelected(item.id);
                  return (
                    <div
                      key={item.id}
                      className={`relative rounded-lg overflow-hidden bg-misty/50 cursor-pointer transition-all ${
                        duplicateSelection.selectMode
                          ? isSel
                            ? 'ring-2 ring-red-400 ring-offset-1 opacity-60'
                            : 'hover:ring-2 hover:ring-green-400/50'
                          : ''
                      }`}
                      onClick={() => {
                        if (duplicateSelection.selectMode) {
                          duplicateSelection.toggleItem(item.id);
                        }
                      }}
                      onPointerDown={() => duplicateSelection.onPointerDown(item.id)}
                      onPointerUp={duplicateSelection.onPointerUp}
                    >
                      <ThumbTile item={item} api={api} />
                      {duplicateSelection.selectMode && (
                        <div className={`absolute top-1.5 left-1.5 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors ${
                          isSel ? 'bg-red-400 border-red-400 text-white' : 'bg-black/30 border-white'
                        }`}>
                          {isSel && <span className="text-[10px] leading-none">✓</span>}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    )}

    {duplicateSelection.selectMode && (
      <div className="fixed bottom-0 left-0 right-0 z-[60] flex justify-center items-center py-3 px-4 bg-white/95 backdrop-blur-md border-t border-misty md:ml-14">
        <button
          onClick={handleDuplicateBatchDelete}
          disabled={duplicateSelection.selectedIds.size === 0}
          className="flex flex-col items-center gap-1 text-sm text-text hover:text-red-500 transition-colors disabled:opacity-30"
        >
          <span className="text-xl">🗑️</span>
          <span className="text-[10px]">删除选中 ({duplicateSelection.selectedIds.size})</span>
        </button>
      </div>
    )}
  </div>
)}
```

- [ ] **Step 3: Add GPU info section to 系统信息 card**

In the "系统信息" section (after line 364, before the closing of the stats display block), add GPU info display. The GPU info goes inside the `{stats ? (` block, after the last `StatRow`:

```tsx
{serverInfo?.gpu && (
  <>
    <div className="border-t border-misty my-2" />
    <div className="flex items-center gap-2 py-1">
      <span className={`w-2 h-2 rounded-full ${serverInfo.gpu.cuda_available ? 'bg-green-400' : 'bg-yellow-400'}`} />
      <span className="text-sm text-text">
        {serverInfo.gpu.cuda_available
          ? `GPU: ${serverInfo.gpu.device_name || 'CUDA'}`
          : 'GPU: 不可用 (CPU 模式)'}
      </span>
    </div>
    {serverInfo.gpu.cuda_available && serverInfo.gpu.memory_total_gb && (
      <StatRow
        label="显存"
        value={`${serverInfo.gpu.memory_used_gb ?? 0} GB / ${serverInfo.gpu.memory_total_gb} GB`}
      />
    )}
    {serverInfo.models.clip_loaded && (
      <StatRow label="Chinese-CLIP" value={`${serverInfo.models.clip_device} 模式`} />
    )}
  </>
)}
```

- [ ] **Step 4: Verify TypeScript compilation**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -20`
Expected: No new errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/SettingsPage.tsx
git commit -m "feat: SettingsPage — 重复照片批量删除交互 + GPU 状态展示卡片"
```

---

### Task 10: End-to-end verification smoke test

- [ ] **Step 1: Start backend and frontend**

```bash
# Terminal 1
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8501

# Terminal 2
cd frontend && npm run dev
```

- [ ] **Step 2: Test favorites flow**

1. Open http://localhost:5173 → verify bottom nav has 6 tabs (❤️ 收藏 between 时间线 and 搜索)
2. Click 收藏 tab → verify empty state "还没有收藏照片哦"
3. Open a photo (click any thumbnail) → verify ♡ button in top bar
4. Click ♡ → verify it becomes ♥ (pink)
5. Close lightbox, go to HomePage → verify "最近收藏" section shows the favorited photo
6. Click "查看全部" → verify navigates to /favorites with the photo in grid
7. In favorites page, long-press to enter select mode → select some → "取消收藏" → verify they disappear

- [ ] **Step 3: Test duplicate delete flow**

1. Go to Settings → scroll to 检测重复照片
2. Click "检测重复照片" → wait, then "查看结果"
3. Click "批量选择" → verify selection mode activates
4. Click on a photo in one pair to select it (red ring)
5. Click "删除选中 (1)" → confirm → verify pair is removed

- [ ] **Step 4: Test GPU display**

1. Go to Settings → scroll to 系统信息
2. Verify GPU status row shows green dot + GPU name (or yellow dot + "CPU 模式")
3. Verify 显存 row shows used/total
4. Verify Chinese-CLIP shows device mode

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "chore: E2E smoke test verified — favorites flow + duplicate delete + GPU display"
```
