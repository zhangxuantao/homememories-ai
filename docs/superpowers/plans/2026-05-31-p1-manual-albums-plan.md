# 手动相册 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现完整的手动相册功能 — 创建/重命名/换封面/删除相册，瀑布流详情页，底部Sheet选择器，导航替换。

**Architecture:** 后端在现有 `albums.py` 新增 3 个 REST 端点（GET/PATCH/DELETE `/{id}`）。前端新增 AlbumsPage、AlbumDetailPage、AlbumPickerSheet 三个组件，遵循现有页面模式（FavoritesPage 风格）。数据库无需变更，`albums`/`album_media` 表已存在。

**Tech Stack:** Python/FastAPI 后端 + React 18/TypeScript/Tailwind 前端

---

### Task 1: 后端 — 补全 albums API 端点

**Files:**
- Modify: `backend/app/routers/albums.py`
- Create: `backend/tests/test_albums.py`

**Depends on:** Nothing

- [ ] **Step 1: 编写测试文件**

```python
# backend/tests/test_albums.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_connection, init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    db_path = tmp_path / "test_albums.db"
    init_db(db_path)

    # Override get_connection dependency
    from app.database import get_connection as original_get_connection
    def _override():
        return original_get_connection(str(db_path))

    import app.routers.albums as albums_module
    app.dependency_overrides[original_get_connection] = _override

    # Seed: create an album and add media entries
    conn = original_get_connection(str(db_path))
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_added) VALUES (?, ?, ?, ?, ?)",
        (1, "/test/img1.jpg", "img1.jpg", "image", "2026-01-01T00:00:00"),
    )
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_added) VALUES (?, ?, ?, ?, ?)",
        (2, "/test/img2.jpg", "img2.jpg", "image", "2026-01-02T00:00:00"),
    )
    conn.execute(
        "INSERT INTO albums (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (1, "测试相册", "2026-01-01T00:00:00", "2026-01-01T00:00:00"),
    )
    conn.execute(
        "INSERT INTO album_media (album_id, media_id, sort_order) VALUES (?, ?, ?)",
        (1, 1, 0),
    )
    conn.commit()
    conn.close()

    yield

    app.dependency_overrides.clear()


def test_get_album():
    resp = client.get("/api/albums/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "测试相册"
    assert data["media_count"] == 1
    assert "cover_thumbnail" in data


def test_get_album_not_found():
    resp = client.get("/api/albums/999")
    assert resp.status_code == 404


def test_patch_album_rename():
    resp = client.patch("/api/albums/1", json={"name": "重命名相册"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "重命名相册"

    # Verify persisted
    get_resp = client.get("/api/albums/1")
    assert get_resp.json()["name"] == "重命名相册"


def test_patch_album_change_cover():
    resp = client.patch("/api/albums/1", json={"cover_media_id": 1})
    assert resp.status_code == 200
    assert resp.json()["cover_media_id"] == 1


def test_patch_album_both():
    resp = client.patch("/api/albums/1", json={"name": "新名字", "cover_media_id": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "新名字"
    assert data["cover_media_id"] == 2


def test_patch_album_not_found():
    resp = client.patch("/api/albums/999", json={"name": "x"})
    assert resp.status_code == 404


def test_delete_album():
    resp = client.delete("/api/albums/1")
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 1

    # Verify gone
    get_resp = client.get("/api/albums/1")
    assert get_resp.status_code == 404


def test_delete_album_not_found():
    resp = client.delete("/api/albums/999")
    assert resp.status_code == 404
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend && python -m pytest tests/test_albums.py -v
```

预期: `test_get_album` 和 `test_delete_album` 返回 404 或 405。

- [ ] **Step 3: 在 albums.py 新增 3 个端点**

在 `backend/app/routers/albums.py` 末尾（`remove_media_from_album` 之后）追加：

```python
@router.get("/{album_id}")
def get_album(album_id: int):
    conn = get_connection()
    row = conn.execute(
        "SELECT a.*, m.thumbnail_path, "
        "(SELECT COUNT(*) FROM album_media WHERE album_id = a.id) AS media_count "
        "FROM albums a LEFT JOIN media m ON a.cover_media_id = m.id "
        "WHERE a.id = ?",
        (album_id,),
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="相册不存在")
    return {
        "id": row["id"],
        "name": row["name"],
        "cover_media_id": row["cover_media_id"],
        "cover_thumbnail": row["thumbnail_path"],
        "media_count": row["media_count"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


class AlbumPatch(BaseModel):
    name: str | None = None
    cover_media_id: int | None = None


@router.patch("/{album_id}")
def update_album(album_id: int, body: AlbumPatch):
    conn = get_connection()
    album = conn.execute("SELECT id FROM albums WHERE id = ?", (album_id,)).fetchone()
    if not album:
        conn.close()
        raise HTTPException(status_code=404, detail="相册不存在")

    now = datetime.now(timezone.utc).isoformat()
    if body.name is not None:
        conn.execute(
            "UPDATE albums SET name = ?, updated_at = ? WHERE id = ?",
            (body.name, now, album_id),
        )
    if body.cover_media_id is not None:
        conn.execute(
            "UPDATE albums SET cover_media_id = ?, updated_at = ? WHERE id = ?",
            (body.cover_media_id, now, album_id),
        )

    conn.commit()

    # Return updated album
    row = conn.execute(
        "SELECT a.*, m.thumbnail_path, "
        "(SELECT COUNT(*) FROM album_media WHERE album_id = a.id) AS media_count "
        "FROM albums a LEFT JOIN media m ON a.cover_media_id = m.id "
        "WHERE a.id = ?",
        (album_id,),
    ).fetchone()
    conn.close()
    return {
        "id": row["id"],
        "name": row["name"],
        "cover_media_id": row["cover_media_id"],
        "cover_thumbnail": row["thumbnail_path"],
        "media_count": row["media_count"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@router.delete("/{album_id}")
def delete_album(album_id: int):
    conn = get_connection()
    album = conn.execute("SELECT id FROM albums WHERE id = ?", (album_id,)).fetchone()
    if not album:
        conn.close()
        raise HTTPException(status_code=404, detail="相册不存在")

    conn.execute("DELETE FROM albums WHERE id = ?", (album_id,))
    conn.commit()
    conn.close()
    return {"deleted": album_id}
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend && python -m pytest tests/test_albums.py -v
```

预期: 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/albums.py backend/tests/test_albums.py
git commit -m "feat(albums): 新增 GET/PATCH/DELETE /api/albums/:id 端点"
```

---

### Task 2: 前端 — API 客户端 + types + useAlbums hook

**Files:**
- Modify: `frontend/src/api/client.ts`
- Create: `frontend/src/hooks/useAlbums.ts`

**Depends on:** Task 1

- [ ] **Step 1: 在 client.ts 添加 Album 类型和 API 方法**

在 `frontend/src/api/client.ts` 的 `FaceCluster` 接口之后添加：

```typescript
export interface Album {
  id: number;
  name: string;
  cover_media_id: number | null;
  cover_thumbnail: string | null;
  media_count: number;
  created_at: string;
  updated_at: string;
}
```

在 `ApiClient` 类的 `deleteDuplicateMedia` 方法之后添加：

```typescript
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
```

- [ ] **Step 2: 创建 useAlbums hook**

```typescript
// frontend/src/hooks/useAlbums.ts
import { useState, useEffect, useCallback } from 'react';
import { api, type Album, type MediaItem } from '../api/client';

export function useAlbums() {
  const [albums, setAlbums] = useState<Album[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.listAlbums();
      setAlbums(data);
    } catch (err) {
      console.error('Failed to load albums:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  return { albums, loading, refresh };
}

export function useAlbumMedia(albumId: number) {
  const [items, setItems] = useState<MediaItem[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getAlbumMedia(albumId, 500);
      setItems(data);
    } catch (err) {
      console.error('Failed to load album media:', err);
    } finally {
      setLoading(false);
    }
  }, [albumId]);

  useEffect(() => { refresh(); }, [refresh]);

  return { items, loading, refresh };
}
```

- [ ] **Step 3: 验证 TypeScript 编译**

```bash
cd frontend && npx tsc --noEmit
```

预期: 无错误

- [ ] **Step 4: Commit**

```bash
git add frontend/src/api/client.ts frontend/src/hooks/useAlbums.ts
git commit -m "feat(albums): 新增 Album 类型、API 方法和 useAlbums hook"
```

---

### Task 3: 前端 — AlbumsPage + 导航替换

**Files:**
- Create: `frontend/src/pages/AlbumsPage.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/layout/MobileNav.tsx`
- Modify: `frontend/src/components/layout/DesktopRail.tsx`

**Depends on:** Task 2

- [ ] **Step 1: 创建 AlbumsPage**

```typescript
// frontend/src/pages/AlbumsPage.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAlbums } from '../hooks/useAlbums';
import { api } from '../api/client';

export default function AlbumsPage() {
  const navigate = useNavigate();
  const { albums, loading, refresh } = useAlbums();
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [menuAlbumId, setMenuAlbumId] = useState<number | null>(null);

  const handleCreate = async () => {
    const name = newName.trim();
    if (!name) return;
    try {
      const album = await api.createAlbum(name);
      setNewName('');
      setShowCreate(false);
      navigate(`/albums/${album.id}`);
    } catch (err) {
      alert('创建失败: ' + (err as Error).message);
    }
  };

  const handleRename = async (id: number) => {
    const name = prompt('新名称:');
    if (!name) return;
    try {
      await api.updateAlbum(id, { name });
      refresh();
    } catch (err) {
      alert('重命名失败: ' + (err as Error).message);
    }
    setMenuAlbumId(null);
  };

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`确定删除相册「${name}」？照片不会被删除。`)) return;
    try {
      await api.deleteAlbum(id);
      refresh();
    } catch (err) {
      alert('删除失败: ' + (err as Error).message);
    }
    setMenuAlbumId(null);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!loading && albums.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[80vh] px-6 text-center">
        <span className="text-6xl mb-4">📁</span>
        <p className="text-lg text-text font-semibold mb-2">还没有相册哦</p>
        <p className="text-sm text-text-light mb-6">创建相册，手动整理你的照片吧</p>
        {!showCreate ? (
          <button
            onClick={() => setShowCreate(true)}
            className="px-6 py-2.5 bg-primary text-white rounded-btn font-medium hover:opacity-90 transition-opacity"
          >
            创建第一个相册
          </button>
        ) : (
          <div className="flex gap-2">
            <input
              autoFocus
              value={newName}
              onChange={e => setNewName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleCreate()}
              placeholder="相册名称"
              className="px-3 py-2 border border-misty rounded-btn text-sm outline-none focus:border-primary"
            />
            <button onClick={handleCreate} className="px-4 py-2 bg-primary text-white rounded-btn text-sm font-medium">创建</button>
            <button onClick={() => { setShowCreate(false); setNewName(''); }} className="px-4 py-2 text-text-light text-sm">取消</button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 md:py-8">
      <div className="flex justify-between items-center mb-6">
        <motion.h1
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-2xl font-bold text-text"
        >
          📁 我的相册
        </motion.h1>

        <button
          onClick={() => {
            setShowCreate(!showCreate);
            setNewName('');
            setMenuAlbumId(null);
          }}
          className="w-9 h-9 flex items-center justify-center rounded-full bg-primary text-white text-lg hover:opacity-90 transition-opacity"
        >
          +
        </button>
      </div>

      <AnimatePresence>
        {showCreate && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden mb-4"
          >
            <div className="flex gap-2 p-3 bg-misty/30 rounded-card">
              <input
                autoFocus
                value={newName}
                onChange={e => setNewName(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleCreate()}
                placeholder="输入相册名称"
                className="flex-1 px-3 py-2 border border-misty rounded-btn text-sm outline-none focus:border-primary bg-white"
              />
              <button onClick={handleCreate} className="px-4 py-2 bg-primary text-white rounded-btn text-sm font-medium">创建</button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {albums.map(album => (
          <div key={album.id} className="relative group">
            <div
              className="rounded-card overflow-hidden bg-misty cursor-pointer hover:opacity-90 transition-opacity"
              onClick={() => navigate(`/albums/${album.id}`)}
              onContextMenu={e => { e.preventDefault(); setMenuAlbumId(menuAlbumId === album.id ? null : album.id); }}
            >
              <div className="aspect-[4/3]">
                {album.cover_thumbnail ? (
                  <img
                    src={api.thumbUrl(album.cover_thumbnail)}
                    alt={album.name}
                    className="w-full h-full object-cover"
                    loading="lazy"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-4xl">📁</div>
                )}
              </div>
              <div className="p-2.5">
                <p className="text-sm font-medium text-text truncate">{album.name}</p>
                <p className="text-xs text-text-light mt-0.5">{album.media_count} 张照片</p>
              </div>
            </div>

            {/* Context menu */}
            <AnimatePresence>
              {menuAlbumId === album.id && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="absolute top-2 right-2 bg-white rounded-card shadow-lg border border-misty py-1 z-10"
                >
                  <button
                    onClick={() => handleRename(album.id)}
                    className="block w-full text-left px-3 py-1.5 text-sm text-text hover:bg-misty/50"
                  >
                    重命名
                  </button>
                  <button
                    onClick={() => handleDelete(album.id, album.name)}
                    className="block w-full text-left px-3 py-1.5 text-sm text-red-500 hover:bg-misty/50"
                  >
                    删除
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 注册路由**

在 `frontend/src/App.tsx` 中：

在 `lazy` imports 区块添加：
```typescript
const AlbumsPage = lazy(() => import('./pages/AlbumsPage'));
```

在 `<Routes>` 内（`</Routes>` 闭合标签前）添加：
```tsx
<Route path="/albums" element={<AnimatedPage><AlbumsPage /></AnimatedPage>} />
```

- [ ] **Step 3: 更新导航 — MobileNav**

在 `MobileNav.tsx` 中，将 TABS 数组第 6 项从：
```typescript
{ to: '/settings', label: '设置', icon: '⚙️' },
```
改为：
```typescript
{ to: '/albums', label: '相册', icon: '📁' },
```

- [ ] **Step 4: 更新导航 — DesktopRail**

在 `DesktopRail.tsx` 中，同样将第 6 项从：
```typescript
{ to: '/settings', label: '设置', icon: '⚙️' },
```
改为：
```typescript
{ to: '/albums', label: '相册', icon: '📁' },
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/AlbumsPage.tsx frontend/src/App.tsx \
        frontend/src/components/layout/MobileNav.tsx \
        frontend/src/components/layout/DesktopRail.tsx
git commit -m "feat(albums): 新增 AlbumsPage + 路由 + 导航替换设置→相册"
```

---

### Task 4: 前端 — AlbumDetailPage（瀑布流详情页）

**Files:**
- Create: `frontend/src/pages/AlbumDetailPage.tsx`

**Depends on:** Task 2 (reuses useAlbums hook and API methods)

- [ ] **Step 1: 创建 AlbumDetailPage**

```typescript
// frontend/src/pages/AlbumDetailPage.tsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { api, type Album, type MediaItem } from '../api/client';
import { useSelection } from '../hooks/useSelection';
import { useAlbumMedia } from '../hooks/useAlbums';
import SelectionBar from '../components/gallery/SelectionBar';

export default function AlbumDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const albumId = Number(id);
  const [album, setAlbum] = useState<Album | null>(null);
  const { items, loading, refresh } = useAlbumMedia(albumId);
  const selection = useSelection();

  useEffect(() => {
    api.getAlbum(albumId).then(setAlbum).catch(() => navigate('/albums'));
  }, [albumId, navigate]);

  const handleRemoveFromAlbum = async () => {
    const ids = Array.from(selection.selectedIds);
    if (!confirm(`从相册中移除这 ${ids.length} 张照片？`)) return;
    try {
      await api.removeFromAlbum(albumId, ids);
      selection.exitSelectMode();
      refresh();
    } catch (err) {
      alert('操作失败: ' + (err as Error).message);
    }
  };

  const handleDeleteAlbum = async () => {
    if (!album) return;
    if (!confirm(`确定删除相册「${album.name}」？照片不会被删除。`)) return;
    try {
      await api.deleteAlbum(albumId);
      navigate('/albums');
    } catch (err) {
      alert('删除失败: ' + (err as Error).message);
    }
  };

  const handleRename = async () => {
    if (!album) return;
    const name = prompt('新名称:', album.name);
    if (!name) return;
    try {
      const updated = await api.updateAlbum(albumId, { name });
      setAlbum(updated);
    } catch (err) {
      alert('重命名失败: ' + (err as Error).message);
    }
  };

  const handleSetCover = async (mediaId: number) => {
    try {
      const updated = await api.updateAlbum(albumId, { cover_media_id: mediaId });
      setAlbum(updated);
    } catch (err) {
      alert('设置封面失败: ' + (err as Error).message);
    }
  };

  const handleAddPhotos = () => {
    // Navigate to search page with intent to add to album
    navigate('/search');
  };

  if (!album) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 md:py-8">
      {/* Back button */}
      <button
        onClick={() => navigate('/albums')}
        className="flex items-center gap-1 text-sm text-text-light hover:text-text mb-4 transition-colors"
      >
        <span>←</span> 返回相册列表
      </button>

      {/* Hero */}
      <div className="relative rounded-card overflow-hidden mb-6 aspect-[3/1] bg-misty">
        {album.cover_thumbnail ? (
          <img
            src={api.thumbUrl(album.cover_thumbnail)}
            alt={album.name}
            className="w-full h-full object-cover blur-sm scale-110"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-6xl">📁</div>
        )}
        <div className="absolute inset-0 bg-black/30 flex items-end p-4">
          <div>
            <h1 className="text-xl font-bold text-white">{album.name}</h1>
            <p className="text-sm text-white/70">{album.media_count} 张照片</p>
          </div>
        </div>

        {/* Action buttons */}
        <div className="absolute top-3 right-3 flex gap-1.5">
          <button
            onClick={handleAddPhotos}
            className="px-3 py-1.5 bg-white/90 text-text text-xs rounded-btn font-medium hover:bg-white transition-colors"
          >
            + 添加照片
          </button>
          <button
            onClick={handleRename}
            className="px-3 py-1.5 bg-white/90 text-text text-xs rounded-btn font-medium hover:bg-white transition-colors"
          >
            重命名
          </button>
          <button
            onClick={handleDeleteAlbum}
            className="px-3 py-1.5 bg-white/90 text-red-500 text-xs rounded-btn font-medium hover:bg-white transition-colors"
          >
            删除
          </button>
        </div>
      </div>

      {/* Selection bar */}
      {selection.selectMode && (
        <SelectionBar
          count={selection.selectedCount}
          onSelectAll={() => selection.selectAll(items.map(i => i.id))}
          onClearAll={() => selection.selectAll([])}
          onExit={selection.exitSelectMode}
        />
      )}

      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {/* Empty state */}
      {!loading && items.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 px-6 text-center">
          <span className="text-5xl mb-4">📁</span>
          <p className="text-lg text-text font-semibold mb-2">相册还是空的</p>
          <p className="text-sm text-text-light mb-6">去搜索页面选中照片加入此相册</p>
          <button
            onClick={() => navigate('/search')}
            className="px-6 py-2.5 bg-primary text-white rounded-btn font-medium hover:opacity-90 transition-opacity"
          >
            去搜索
          </button>
        </div>
      )}

      {/* Masonry grid */}
      {!loading && items.length > 0 && (
        <div
          className="columns-2 md:columns-4 gap-2"
          style={selection.selectMode ? { marginTop: '3rem', marginBottom: '3.5rem' } : undefined}
        >
          {items.map(item => {
            const isSel = selection.isSelected(item.id);
            return (
              <div
                key={item.id}
                className={`break-inside-avoid mb-2 rounded-card overflow-hidden bg-misty relative group cursor-pointer transition-all ${
                  selection.selectMode
                    ? isSel
                      ? 'ring-2 ring-primary ring-offset-1'
                      : 'opacity-50'
                    : 'hover:opacity-90'
                }`}
                onClick={() =>
                  selection.handleItemClick(item.id, () =>
                    navigate(`/photo/${item.id}`, { state: { from: `/albums/${albumId}` } })
                  )
                }
                onPointerDown={() => selection.onPointerDown(item.id)}
                onPointerUp={selection.onPointerUp}
                onContextMenu={e => {
                  if (!selection.selectMode) {
                    e.preventDefault();
                    handleSetCover(item.id);
                  }
                }}
              >
                {item.thumbnail_path ? (
                  <img
                    src={api.thumbUrl(item.thumbnail_path)}
                    alt={item.filename}
                    className="w-full h-auto"
                    loading="lazy"
                    draggable={false}
                  />
                ) : (
                  <div className="w-full aspect-square flex items-center justify-center text-3xl">📷</div>
                )}

                {selection.selectMode && (
                  <div className={`absolute top-1.5 left-1.5 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors ${
                    isSel ? 'bg-primary border-primary text-white' : 'bg-black/30 border-white'
                  }`}>
                    {isSel && <span className="text-[10px] leading-none">✓</span>}
                  </div>
                )}

                {!selection.selectMode && (
                  <button
                    onClick={e => { e.stopPropagation(); handleSetCover(item.id); }}
                    className="absolute top-1.5 right-1.5 w-6 h-6 rounded-full bg-black/40 text-white text-[10px] opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                    title="设为封面"
                  >
                    ⭐
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Bottom action bar in selection mode */}
      {selection.selectMode && (
        <div className="fixed bottom-0 left-0 right-0 z-[60] flex justify-around items-center py-3 px-4 bg-white/95 backdrop-blur-md border-t border-misty md:ml-14">
          <button
            onClick={handleRemoveFromAlbum}
            className="flex flex-col items-center gap-1 text-sm text-text hover:text-red-500 transition-colors"
          >
            <span className="text-xl">📤</span>
            <span className="text-[10px]">从相册移除 ({selection.selectedCount})</span>
          </button>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: 注册 AlbumDetailPage 路由**

在 `frontend/src/App.tsx` 中：

**添加 lazy import:**
```typescript
const AlbumDetailPage = lazy(() => import('./pages/AlbumDetailPage'));
```

**在 `<Routes>` 内（在 `/albums` route 之后）添加:**
```tsx
<Route path="/albums/:id" element={<AlbumDetailPage />} />
```

- [ ] **Step 3: 验证 TypeScript 编译**

```bash
cd frontend && npx tsc --noEmit
```

预期: 无错误

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/AlbumDetailPage.tsx
git commit -m "feat(albums): 新增 AlbumDetailPage 瀑布流详情页"
```

---

### Task 5: 前端 — AlbumPickerSheet + 集成 SearchPage/PeoplePage

**Files:**
- Create: `frontend/src/components/albums/AlbumPickerSheet.tsx`
- Modify: `frontend/src/pages/SearchPage.tsx`
- Modify: `frontend/src/pages/PeoplePage.tsx`

**Depends on:** Task 2

- [ ] **Step 1: 创建 AlbumPickerSheet 组件**

```typescript
// frontend/src/components/albums/AlbumPickerSheet.tsx
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { api, type Album } from '../../api/client';

interface AlbumPickerSheetProps {
  open: boolean;
  onClose: () => void;
  mediaIds: number[];
  onDone: () => void;
}

export default function AlbumPickerSheet({ open, onClose, mediaIds, onDone }: AlbumPickerSheetProps) {
  const [albums, setAlbums] = useState<Album[]>([]);
  const [loading, setLoading] = useState(true);
  const [newName, setNewName] = useState('');
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    if (open) {
      setLoading(true);
      api.listAlbums().then(setAlbums).finally(() => setLoading(false));
      setNewName('');
    }
  }, [open]);

  const handleAdd = async (albumId: number, albumName: string) => {
    setAdding(true);
    try {
      await api.addToAlbum(albumId, mediaIds);
      alert(`已添加 ${mediaIds.length} 张到「${albumName}」`);
      onDone();
      onClose();
    } catch (err) {
      alert('添加失败: ' + (err as Error).message);
    } finally {
      setAdding(false);
    }
  };

  const handleCreateAndAdd = async () => {
    const name = newName.trim();
    if (!name) return;
    setAdding(true);
    try {
      const album = await api.createAlbum(name);
      await api.addToAlbum(album.id, mediaIds);
      alert(`已创建「${name}」并添加 ${mediaIds.length} 张照片`);
      onDone();
      onClose();
    } catch (err) {
      alert('操作失败: ' + (err as Error).message);
    } finally {
      setAdding(false);
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[70] bg-black/40"
            onClick={onClose}
          />

          {/* Sheet */}
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed bottom-0 left-0 right-0 z-[80] bg-white rounded-t-2xl max-h-[60vh] flex flex-col md:ml-14"
          >
            {/* Handle */}
            <div className="flex justify-center pt-3 pb-1">
              <div className="w-10 h-1 rounded-full bg-gray-300" />
            </div>

            <h3 className="px-4 py-2 text-base font-semibold text-text">
              加入相册 ({mediaIds.length} 张)
            </h3>

            {/* Create new */}
            <div className="px-4 pb-3 flex gap-2">
              <input
                value={newName}
                onChange={e => setNewName(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleCreateAndAdd()}
                placeholder="新建相册..."
                className="flex-1 px-3 py-2 border border-misty rounded-btn text-sm outline-none focus:border-primary"
                disabled={adding}
              />
              <button
                onClick={handleCreateAndAdd}
                disabled={!newName.trim() || adding}
                className="px-4 py-2 bg-primary text-white rounded-btn text-sm font-medium disabled:opacity-50"
              >
                创建
              </button>
            </div>

            {/* Album list */}
            <div className="flex-1 overflow-y-auto px-4 pb-6">
              {loading ? (
                <div className="flex justify-center py-8">
                  <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                </div>
              ) : albums.length === 0 ? (
                <p className="text-center text-text-light py-8 text-sm">暂无相册，在上面新建一个</p>
              ) : (
                <div className="space-y-1">
                  {albums.map(album => (
                    <button
                      key={album.id}
                      onClick={() => handleAdd(album.id, album.name)}
                      disabled={adding}
                      className="w-full flex items-center gap-3 p-2.5 rounded-btn hover:bg-misty/50 transition-colors text-left"
                    >
                      <div className="w-12 h-12 rounded-lg bg-misty flex-shrink-0 overflow-hidden">
                        {album.cover_thumbnail ? (
                          <img
                            src={api.thumbUrl(album.cover_thumbnail)}
                            alt=""
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-xl">📁</div>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-text truncate">{album.name}</p>
                        <p className="text-xs text-text-light">{album.media_count} 张</p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
```

- [ ] **Step 2: 更改 SearchPage — 用 AlbumPickerSheet 替换 prompt**

在 `SearchPage.tsx` 中：

**添加 import:**
```typescript
import AlbumPickerSheet from '../components/albums/AlbumPickerSheet';
```

**添加 state:**
```typescript
const [albumPickerOpen, setAlbumPickerOpen] = useState(false);
const [pendingAlbumIds, setPendingAlbumIds] = useState<number[]>([]);
```

**替换 `handleAddToAlbum` 函数:**
```typescript
  const handleAddToAlbum = () => {
    const ids = Array.from(selection.selectedIds);
    setPendingAlbumIds(ids);
    setAlbumPickerOpen(true);
  };
```

**在 `</div>` 闭合之前（最外层 div 结尾之前）添加 AlbumPickerSheet:**
```tsx
      <AlbumPickerSheet
        open={albumPickerOpen}
        onClose={() => setAlbumPickerOpen(false)}
        mediaIds={pendingAlbumIds}
        onDone={() => selection.exitSelectMode()}
      />
```

- [ ] **Step 3: 更改 PeoplePage — 集成 AlbumPickerSheet**

在 `PeoplePage.tsx` 中：

**添加 import:**
```typescript
import AlbumPickerSheet from '../components/albums/AlbumPickerSheet';
```

**添加 state:**
```typescript
const [albumPickerOpen, setAlbumPickerOpen] = useState(false);
const [pendingAlbumIds, setPendingAlbumIds] = useState<number[]>([]);
```

**替换 `onAddToAlbum={() => {}}` 为:**
```tsx
onAddToAlbum={() => {
  const ids = Array.from(selection.selectedIds);
  setPendingAlbumIds(ids);
  setAlbumPickerOpen(true);
}}
```

**在页面组件最外层 div 结尾前添加:**
```tsx
      <AlbumPickerSheet
        open={albumPickerOpen}
        onClose={() => setAlbumPickerOpen(false)}
        mediaIds={pendingAlbumIds}
        onDone={() => selection.exitSelectMode()}
      />
```

- [ ] **Step 4: 验证 TypeScript 编译和构建**

```bash
cd frontend && npx tsc --noEmit
```

预期: 无错误

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/albums/AlbumPickerSheet.tsx \
        frontend/src/pages/SearchPage.tsx \
        frontend/src/pages/PeoplePage.tsx
git commit -m "feat(albums): 新增 AlbumPickerSheet + 集成 SearchPage/PeoplePage"
```

---

### Task 6: 前端 — HomePage 设置入口

**Files:**
- Modify: `frontend/src/pages/HomePage.tsx`

**Depends on:** Task 3 (导航已改为相册)

- [ ] **Step 1: 在 HomePage 标题栏添加设置齿轮图标**

在 `HomePage.tsx` 中：

**添加 import:**
```typescript
import { Link } from 'react-router-dom';
```

**将标题 `<motion.h1>` 行替换为:**
```tsx
        <div className="flex justify-between items-center mb-6">
          <motion.h1
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-2xl font-bold text-text"
          >
            家庭回忆
          </motion.h1>
          <Link
            to="/settings"
            className="w-9 h-9 flex items-center justify-center rounded-full hover:bg-misty transition-colors text-lg"
            title="设置"
          >
            ⚙️
          </Link>
        </div>
```

- [ ] **Step 2: 验证编译**

```bash
cd frontend && npx tsc --noEmit
```

预期: 无错误

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/HomePage.tsx
git commit -m "feat(albums): HomePage 右上角添加设置入口"
```

---

### Task 7: 端到端验证

**Depends on:** Task 1-6 all complete

- [ ] **Step 1: 运行后端测试**

```bash
cd backend && python -m pytest tests/ -v
```

预期: 所有测试通过（包含新增的 8 个 albums 测试）

- [ ] **Step 2: 验证后端 API 手动测试**

```bash
# 启动后端
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8501 &

# 测试列表
curl -s http://localhost:8501/api/albums | head -1

# 创建相册
curl -s -X POST http://localhost:8501/api/albums -H 'Content-Type: application/json' -d '{"name":"测试"}' 

# 获取详情
curl -s http://localhost:8501/api/albums/1

# 重命名
curl -s -X PATCH http://localhost:8501/api/albums/1 -H 'Content-Type: application/json' -d '{"name":"改名"}'

# 删除
curl -s -X DELETE http://localhost:8501/api/albums/1
```

- [ ] **Step 3: 验证前端构建**

```bash
cd frontend && npm run build
```

预期: 构建成功，无错误

- [ ] **Step 4: Commit（如有修正）**

```bash
git add -A
git commit -m "chore: E2E 验证通过 — albums 全部端点 + 前端编译"
```
