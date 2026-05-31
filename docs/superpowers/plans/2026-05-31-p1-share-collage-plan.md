# 分享/导出 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现局域网分享链接和拼图功能 — 创建临时分享链接（token URL）、公开查看页、PIL 拼图生成。

**Architecture:** 后端新建 `shares` 表 + `shares.py` 路由（认证 CRUD + 公开查看端点），`media.py` 新增 collage 端点。前端新增 ShareViewPage（公开页）、SharePanel（创建分享 Sheet）、CollagePanel（拼图 Sheet），集成到 Lightbox/SelectionActions/SearchPage/PeoplePage。

**Tech Stack:** Python/FastAPI/Pillow 后端 + React 18/TypeScript/Tailwind 前端

---

### Task 1: 后端 — shares 表 + 分享 API

**Files:**
- Modify: `backend/app/database.py`
- Create: `backend/app/routers/shares.py`
- Create: `backend/tests/test_shares.py`
- Modify: `backend/app/main.py`

**Depends on:** Nothing

- [ ] **Step 1: 在 database.py 添加 shares 表**

在 `backend/app/database.py` 的 SCHEMA 字符串末尾（`CREATE INDEX IF NOT EXISTS idx_favorites_created` 之后）添加：

```sql
CREATE TABLE IF NOT EXISTS shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT UNIQUE NOT NULL,
    title TEXT,
    media_ids TEXT NOT NULL,
    expires_at TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_shares_token ON shares(token);
```

- [ ] **Step 2: 创建 shares.py 路由**

```python
# backend/app/routers/shares.py
import secrets
import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_connection

router = APIRouter(prefix="/api/shares", tags=["shares"])


class ShareCreate(BaseModel):
    media_ids: list[int]
    title: str | None = None
    expires_in_hours: int | None = None  # None = 永久


def _share_row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "token": row["token"],
        "title": row["title"],
        "media_ids": json.loads(row["media_ids"]),
        "expires_at": row["expires_at"],
        "is_active": bool(row["is_active"]),
        "created_at": row["created_at"],
    }


@router.post("")
def create_share(body: ShareCreate):
    if not body.media_ids:
        raise HTTPException(status_code=400, detail="至少选择一张照片")

    token = secrets.token_urlsafe(12)  # 16 chars
    now = datetime.now(timezone.utc).isoformat()
    expires_at = None
    if body.expires_in_hours:
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=body.expires_in_hours)).isoformat()

    conn = get_connection()
    conn.execute(
        "INSERT INTO shares (token, title, media_ids, expires_at, is_active, created_at) "
        "VALUES (?, ?, ?, ?, 1, ?)",
        (token, body.title, json.dumps(body.media_ids), expires_at, now),
    )
    conn.commit()
    conn.close()

    return {"token": token, "url": f"/share/{token}"}


@router.get("")
def list_shares():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM shares WHERE is_active = 1 ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [_share_row_to_dict(r) for r in rows]


@router.delete("/{share_id}")
def revoke_share(share_id: int):
    conn = get_connection()
    row = conn.execute("SELECT id FROM shares WHERE id = ?", (share_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="分享不存在")

    conn.execute("UPDATE shares SET is_active = 0 WHERE id = ?", (share_id,))
    conn.commit()
    conn.close()
    return {"revoked": share_id}


# Public endpoint (no auth, separate prefix to avoid collision)
public_router = APIRouter(tags=["share"])


@public_router.get("/api/share/{token}")
def view_share(token: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM shares WHERE token = ? AND is_active = 1", (token,)
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="分享不存在或已失效")

    # Check expiry
    if row["expires_at"]:
        expires_at = datetime.fromisoformat(row["expires_at"])
        if expires_at < datetime.now(timezone.utc):
            conn.close()
            raise HTTPException(status_code=410, detail="分享链接已过期")

    media_ids = json.loads(row["media_ids"])
    placeholders = ",".join("?" * len(media_ids))
    media_rows = conn.execute(
        f"SELECT id, filename, width, height, media_type, thumbnail_path, date_taken "
        f"FROM media WHERE id IN ({placeholders})",
        media_ids,
    ).fetchall()
    conn.close()

    return {
        "title": row["title"],
        "expires_at": row["expires_at"],
        "created_at": row["created_at"],
        "media": [
            {
                "id": m["id"],
                "filename": m["filename"],
                "width": m["width"],
                "height": m["height"],
                "media_type": m["media_type"],
                "thumbnail_path": m["thumbnail_path"],
                "date_taken": m["date_taken"],
            }
            for m in media_rows
        ],
    }
```

- [ ] **Step 3: 在 main.py 注册路由**

在 `backend/app/main.py` 中找到路由注册区域，添加：

```python
from app.routers import shares

app.include_router(shares.router)
app.include_router(shares.public_router)
```

- [ ] **Step 4: 编写测试**

```python
# backend/tests/test_shares.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_connection, init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    db_path = tmp_path / "test_shares.db"
    init_db(db_path)

    from app.database import get_connection as original_get_connection
    def _override():
        return original_get_connection(str(db_path))

    app.dependency_overrides[original_get_connection] = _override

    conn = original_get_connection(str(db_path))
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_added) VALUES (?, ?, ?, ?, ?)",
        (1, "/test/a.jpg", "a.jpg", "image", "2026-01-01T00:00:00"),
    )
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_added) VALUES (?, ?, ?, ?, ?)",
        (2, "/test/b.jpg", "b.jpg", "image", "2026-01-02T00:00:00"),
    )
    conn.commit()
    conn.close()

    yield
    app.dependency_overrides.clear()


def test_create_share():
    resp = client.post("/api/shares", json={"media_ids": [1, 2], "title": "测试分享"})
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert len(data["token"]) == 16
    assert "/share/" in data["url"]


def test_create_share_empty():
    resp = client.post("/api/shares", json={"media_ids": []})
    assert resp.status_code == 400


def test_list_shares():
    client.post("/api/shares", json={"media_ids": [1]})
    resp = client.get("/api/shares")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_view_share():
    create_resp = client.post("/api/shares", json={"media_ids": [1, 2]})
    token = create_resp.json()["token"]

    resp = client.get(f"/api/share/{token}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["media"]) == 2
    assert data["media"][0]["filename"] == "a.jpg"


def test_view_share_invalid_token():
    resp = client.get("/api/share/nonexistent123")
    assert resp.status_code == 404


def test_view_share_expired():
    # Create with 0 hours expiry (instant expiration edge case: we use -1 hours)
    import json
    from datetime import datetime, timedelta, timezone
    conn = get_connection()
    expired = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    conn.execute(
        "INSERT INTO shares (token, media_ids, expires_at, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
        ("expiredtoken", json.dumps([1]), expired, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()

    resp = client.get("/api/share/expiredtoken")
    assert resp.status_code == 410


def test_revoke_share():
    create_resp = client.post("/api/shares", json={"media_ids": [1]})
    share_id = client.get("/api/shares").json()[0]["id"]

    resp = client.delete(f"/api/shares/{share_id}")
    assert resp.status_code == 200

    # Verify not in list
    list_resp = client.get("/api/shares")
    assert len(list_resp.json()) == 0


def test_revoke_nonexistent():
    resp = client.delete("/api/shares/999")
    assert resp.status_code == 404
```

- [ ] **Step 5: 运行测试验证**

```bash
cd backend && python -m pytest tests/test_shares.py -v
```

预期: 8 tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/database.py backend/app/routers/shares.py backend/app/main.py backend/tests/test_shares.py
git commit -m "feat(shares): 新增 shares 表 + 分享 API（创建/列表/撤销/公开查看）"
```

---

### Task 2: 后端 — 拼图端点

**Files:**
- Modify: `backend/app/routers/media.py`
- Create: `backend/tests/test_collage.py`

**Depends on:** Nothing (independent of Task 1)

- [ ] **Step 1: 编写测试**

```python
# backend/tests/test_collage.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_connection, init_db
from PIL import Image
import io
import os

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    db_path = tmp_path / "test_collage.db"
    init_db(db_path)

    from app.database import get_connection as original_get_connection
    def _override():
        return original_get_connection(str(db_path))

    app.dependency_overrides[original_get_connection] = _override

    # Create test images
    img1_path = tmp_path / "img1.jpg"
    img2_path = tmp_path / "img2.jpg"
    Image.new("RGB", (200, 150), color="red").save(img1_path, "JPEG")
    Image.new("RGB", (300, 200), color="blue").save(img2_path, "JPEG")

    conn = original_get_connection(str(db_path))
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_added) VALUES (?, ?, ?, ?, ?)",
        (1, str(img1_path), "img1.jpg", "image", "2026-01-01T00:00:00"),
    )
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_added) VALUES (?, ?, ?, ?, ?)",
        (2, str(img2_path), "img2.jpg", "image", "2026-01-02T00:00:00"),
    )
    conn.commit()
    conn.close()

    yield
    app.dependency_overrides.clear()


def test_collage_grid():
    resp = client.post("/api/media/collage", json={"media_ids": [1, 2], "layout": "grid"})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"

    img = Image.open(io.BytesIO(resp.content))
    assert img.width > 0 and img.height > 0


def test_collage_horizontal():
    resp = client.post("/api/media/collage", json={"media_ids": [1, 2], "layout": "horizontal"})
    assert resp.status_code == 200
    img = Image.open(io.BytesIO(resp.content))
    # Horizontal: height should be ~200 (max individual height capped)
    assert img.height <= 400


def test_collage_vertical():
    resp = client.post("/api/media/collage", json={"media_ids": [1, 2], "layout": "vertical"})
    assert resp.status_code == 200
    img = Image.open(io.BytesIO(resp.content))
    assert img.width <= 400


def test_collage_default_layout():
    resp = client.post("/api/media/collage", json={"media_ids": [1]})
    assert resp.status_code == 200


def test_collage_empty():
    resp = client.post("/api/media/collage", json={"media_ids": []})
    assert resp.status_code == 400


def test_collage_nonexistent_media():
    resp = client.post("/api/media/collage", json={"media_ids": [999]})
    assert resp.status_code == 404
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend && python -m pytest tests/test_collage.py -v
```

预期: FAIL（端点不存在）

- [ ] **Step 3: 在 media.py 添加 collage 端点**

在 `backend/app/routers/media.py` 末尾追加：

```python
from pydantic import BaseModel as PydanticModel

class CollageRequest(PydanticModel):
    media_ids: list[int]
    layout: str = "grid"  # "grid" | "horizontal" | "vertical"


@router.post("/collage")
def create_collage(body: CollageRequest):
    """Generate a photo collage from selected media."""
    from app.database import get_connection
    from app.config import settings
    from PIL import Image
    import io as io_module
    import math

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
        cols = math.ceil(math.sqrt(n))
        rows_count = math.ceil(n / cols)
        cell_w = min(img.width for img in images)
        cell_h = min(img.height for img in images)

        # Resize all to same cell size
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
```

确保文件顶部已有 `import os`, `import io`, `from fastapi import HTTPException`。检查 `from fastapi.responses import StreamingResponse` 是否已导入（zip 端点已经用了）。

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend && python -m pytest tests/test_collage.py -v
```

预期: 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/media.py backend/tests/test_collage.py
git commit -m "feat(collage): 新增拼图端点 POST /api/media/collage"
```

---

### Task 3: 前端 — API 方法 + ShareViewPage

**Files:**
- Modify: `frontend/src/api/client.ts`
- Create: `frontend/src/pages/ShareViewPage.tsx`
- Modify: `frontend/src/App.tsx`

**Depends on:** Task 1

- [ ] **Step 1: 在 client.ts 添加类型和方法**

在 `Album` 接口之后添加：

```typescript
export interface ShareItem {
  id: number;
  token: string;
  title: string | null;
  media_ids: number[];
  expires_at: string | null;
  is_active: boolean;
  created_at: string;
}
```

在 `ApiClient` 类的 albums 方法区块之后添加：

```typescript
  // ── Shares ──

  async createShare(mediaIds: number[], title?: string, expiresInHours?: number): Promise<{ token: string; url: string }> {
    return this.post<{ token: string; url: string }>('/api/shares', {
      media_ids: mediaIds,
      title,
      expires_in_hours: expiresInHours,
    });
  }

  async listShares(): Promise<ShareItem[]> {
    return this.get<ShareItem[]>('/api/shares');
  }

  async revokeShare(id: number): Promise<{ revoked: number }> {
    return this.delete<{ revoked: number }>(`/api/shares/${id}`);
  }

  async getSharedMedia(token: string): Promise<{ title: string | null; expires_at: string | null; created_at: string; media: MediaItem[] }> {
    return this.get<{ title: string | null; expires_at: string | null; created_at: string; media: MediaItem[] }>(`/api/share/${token}`);
  }

  // ── Collage ──

  async createCollage(mediaIds: number[], layout: string = 'grid'): Promise<Blob> {
    const base = this['baseUrl'] || window.location.origin;
    const res = await fetch(`${base}/api/media/collage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ media_ids: mediaIds, layout }),
    });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return res.blob();
  }
```

- [ ] **Step 2: 创建 ShareViewPage**

```typescript
// frontend/src/pages/ShareViewPage.tsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api, type MediaItem } from '../api/client';
import PhotoGrid from '../components/gallery/PhotoGrid';

export default function ShareViewPage() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const [media, setMedia] = useState<MediaItem[]>([]);
  const [title, setTitle] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    api.getSharedMedia(token)
      .then(data => {
        setMedia(data.media);
        setTitle(data.title);
        setExpiresAt(data.expires_at);
      })
      .catch(err => {
        if (err.message.includes('410')) {
          setError('此分享链接已过期');
        } else {
          setError('分享不存在或已失效');
        }
      })
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen px-6 text-center">
        <span className="text-6xl mb-4">🔗</span>
        <p className="text-lg text-text font-semibold mb-2">{error}</p>
        <p className="text-sm text-text-light">请联系分享者获取新的链接</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-text">
              {title || '分享的照片'}
            </h1>
            <p className="text-sm text-text-light mt-1">
              {media.length} 张照片
              {expiresAt && ` · 过期时间: ${new Date(expiresAt).toLocaleString('zh-CN')}`}
            </p>
          </div>
        </div>

        <PhotoGrid
          items={media}
          onItemClick={(id) => navigate(`/photo/${id}`, { state: { from: `/share/${token}` } })}
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 3: 注册路由**

在 `App.tsx` 中：

**添加 lazy import:**
```typescript
const ShareViewPage = lazy(() => import('./pages/ShareViewPage'));
```

**添加路由**（在 `<Routes>` 内，`AnimatedPage` 包裹的路由之外，因为分享页需要独立样式）:
```tsx
<Route path="/share/:token" element={<ShareViewPage />} />
```

- [ ] **Step 4: 验证 TypeScript 编译**

```bash
cd frontend && npx tsc --noEmit
```

预期: 无错误

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/client.ts frontend/src/pages/ShareViewPage.tsx frontend/src/App.tsx
git commit -m "feat(shares): 新增 ShareViewPage 分享查看页 + API 方法"
```

---

### Task 4: 前端 — SharePanel + CollagePanel 组件

**Files:**
- Create: `frontend/src/components/share/SharePanel.tsx`
- Create: `frontend/src/components/share/CollagePanel.tsx`

**Depends on:** Task 3

- [ ] **Step 1: 创建目录**

```bash
mkdir -p frontend/src/components/share
```

- [ ] **Step 2: 创建 SharePanel**

```typescript
// frontend/src/components/share/SharePanel.tsx
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../../api/client';

interface SharePanelProps {
  open: boolean;
  onClose: () => void;
  mediaIds: number[];
}

const EXPIRY_OPTIONS = [
  { label: '1小时', value: 1 },
  { label: '24小时', value: 24 },
  { label: '7天', value: 168 },
  { label: '永久', value: 0 },
];

export default function SharePanel({ open, onClose, mediaIds }: SharePanelProps) {
  const [title, setTitle] = useState('');
  const [expiry, setExpiry] = useState(24);
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (open) {
      setTitle('');
      setExpiry(24);
      setShareUrl(null);
      setCopied(false);
    }
  }, [open]);

  const handleCreate = async () => {
    setCreating(true);
    try {
      const result = await api.createShare(
        mediaIds,
        title.trim() || undefined,
        expiry === 0 ? undefined : expiry,
      );
      const fullUrl = `${window.location.origin}${result.url}`;
      setShareUrl(fullUrl);
    } catch (err) {
      alert('创建分享失败: ' + (err as Error).message);
    } finally {
      setCreating(false);
    }
  };

  const handleCopy = async () => {
    if (!shareUrl) return;
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      alert('复制失败，请手动复制');
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[70] bg-black/40"
            onClick={onClose}
          />

          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed bottom-0 left-0 right-0 z-[80] bg-white rounded-t-2xl max-h-[70vh] flex flex-col md:ml-14"
          >
            <div className="flex justify-center pt-3 pb-1">
              <div className="w-10 h-1 rounded-full bg-gray-300" />
            </div>

            <h3 className="px-4 py-2 text-base font-semibold text-text">
              分享照片 ({mediaIds.length} 张)
            </h3>

            <div className="flex-1 overflow-y-auto px-4 pb-6">
              {!shareUrl ? (
                <>
                  {/* Title input */}
                  <div className="mb-4">
                    <label className="text-xs text-text-light mb-1 block">标题（可选）</label>
                    <input
                      value={title}
                      onChange={e => setTitle(e.target.value)}
                      placeholder="给这次分享起个名字"
                      className="w-full px-3 py-2 border border-misty rounded-btn text-sm outline-none focus:border-primary"
                    />
                  </div>

                  {/* Expiry selector */}
                  <div className="mb-4">
                    <label className="text-xs text-text-light mb-2 block">有效期</label>
                    <div className="flex gap-2">
                      {EXPIRY_OPTIONS.map(opt => (
                        <button
                          key={opt.value}
                          onClick={() => setExpiry(opt.value)}
                          className={`flex-1 py-2 rounded-btn text-sm font-medium transition-colors ${
                            expiry === opt.value
                              ? 'bg-primary text-white'
                              : 'bg-misty text-text'
                          }`}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <button
                    onClick={handleCreate}
                    disabled={creating}
                    className="w-full py-2.5 bg-primary text-white rounded-btn font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
                  >
                    {creating ? '创建中...' : '创建分享链接'}
                  </button>
                </>
              ) : (
                <>
                  <p className="text-sm text-text-light mb-3">分享链接已生成：</p>
                  <div className="flex gap-2 mb-3">
                    <input
                      readOnly
                      value={shareUrl}
                      className="flex-1 px-3 py-2 border border-misty rounded-btn text-xs outline-none bg-misty/30"
                    />
                    <button
                      onClick={handleCopy}
                      className={`px-4 py-2 rounded-btn text-sm font-medium transition-colors ${
                        copied ? 'bg-green-100 text-green-700' : 'bg-primary text-white'
                      }`}
                    >
                      {copied ? '已复制 ✓' : '复制'}
                    </button>
                  </div>
                  <p className="text-xs text-text-light">
                    局域网内其他设备打开此链接即可查看照片
                  </p>
                </>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
```

- [ ] **Step 3: 创建 CollagePanel**

```typescript
// frontend/src/components/share/CollagePanel.tsx
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../../api/client';

interface CollagePanelProps {
  open: boolean;
  onClose: () => void;
  mediaIds: number[];
}

const LAYOUTS = [
  { label: '网格', value: 'grid', icon: '🔲' },
  { label: '横向', value: 'horizontal', icon: '↔️' },
  { label: '纵向', value: 'vertical', icon: '↕️' },
];

export default function CollagePanel({ open, onClose, mediaIds }: CollagePanelProps) {
  const [layout, setLayout] = useState('grid');
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (open) {
      setLayout('grid');
    }
  }, [open]);

  const handleDownload = async () => {
    setGenerating(true);
    try {
      const blob = await api.createCollage(mediaIds, layout);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `collage_${Date.now()}.jpg`;
      a.click();
      URL.revokeObjectURL(url);
      onClose();
    } catch (err) {
      alert('生成拼图失败: ' + (err as Error).message);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[70] bg-black/40"
            onClick={onClose}
          />

          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed bottom-0 left-0 right-0 z-[80] bg-white rounded-t-2xl flex flex-col md:ml-14"
          >
            <div className="flex justify-center pt-3 pb-1">
              <div className="w-10 h-1 rounded-full bg-gray-300" />
            </div>

            <h3 className="px-4 py-2 text-base font-semibold text-text">
              拼图 ({mediaIds.length} 张)
            </h3>

            <div className="px-4 pb-6">
              <label className="text-xs text-text-light mb-2 block">布局</label>
              <div className="flex gap-2 mb-4">
                {LAYOUTS.map(opt => (
                  <button
                    key={opt.value}
                    onClick={() => setLayout(opt.value)}
                    className={`flex-1 py-3 rounded-btn flex flex-col items-center gap-1 transition-colors ${
                      layout === opt.value
                        ? 'bg-primary/10 text-primary border border-primary'
                        : 'bg-misty text-text border border-transparent'
                    }`}
                  >
                    <span className="text-lg">{opt.icon}</span>
                    <span className="text-xs font-medium">{opt.label}</span>
                  </button>
                ))}
              </div>

              <button
                onClick={handleDownload}
                disabled={generating}
                className="w-full py-2.5 bg-primary text-white rounded-btn font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                {generating ? '生成中...' : '下载拼图'}
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
```

注意：CollagePanel 需要导入 `useEffect`：

```typescript
import { useState, useEffect } from 'react';
```

- [ ] **Step 4: 验证 TypeScript 编译**

```bash
cd frontend && npx tsc --noEmit
```

预期: 无错误

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/share/SharePanel.tsx frontend/src/components/share/CollagePanel.tsx
git commit -m "feat(shares): 新增 SharePanel + CollagePanel 组件"
```

---

### Task 5: 前端 — 集成到现有页面

**Files:**
- Modify: `frontend/src/components/gallery/Lightbox.tsx`
- Modify: `frontend/src/components/gallery/SelectionActions.tsx`
- Modify: `frontend/src/pages/SearchPage.tsx`
- Modify: `frontend/src/pages/PeoplePage.tsx`

**Depends on:** Task 4

- [ ] **Step 1: Lightbox 添加分享按钮**

在 `Lightbox.tsx` 中：

**添加 import:**
```typescript
import SharePanel from '../share/SharePanel';
```

**添加 state** (在 `similarItems` state 之后):
```typescript
const [shareOpen, setShareOpen] = useState(false);
```

**在顶栏按钮区（"下载"按钮旁边）添加分享按钮:**
```tsx
            <button
              onClick={(e) => { e.stopPropagation(); setShareOpen(true); }}
              className="hover:text-primary transition-colors"
            >
              分享
            </button>
```

**在 Lightbox 的 return 语句中**，把 `<AnimatePresence>` 包裹在一个 Fragment 中，SharePanel 作为同级节点：

```tsx
  return (
    <>
      <AnimatePresence>
        <motion.div ...>
          {/* existing content */}
        </motion.div>
      </AnimatePresence>

      <SharePanel
        open={shareOpen}
        onClose={() => setShareOpen(false)}
        mediaIds={[item.id]}
      />
    </>
  );
```

- [ ] **Step 2: SelectionActions 添加分享和拼图按钮**

在 `SelectionActions.tsx` 中：

**在 interface 添加两个新 prop:**
```typescript
interface SelectionActionsProps {
  onAddToAlbum: () => void;
  onShare: () => void;
  onCollage: () => void;
  onDownload: () => void;
  onDelete: () => void;
}
```

**在 JSX 中添加两个新按钮**（在"加入相册"按钮之后，"下载"之前）:
```tsx
      <button
        onClick={onShare}
        className="flex flex-col items-center gap-1 text-sm text-text hover:text-primary transition-colors"
      >
        <span className="text-xl">🔗</span>
        <span className="text-[10px]">分享</span>
      </button>
      <button
        onClick={onCollage}
        className="flex flex-col items-center gap-1 text-sm text-text hover:text-primary transition-colors"
      >
        <span className="text-xl">🖼️</span>
        <span className="text-[10px]">拼图</span>
      </button>
```

- [ ] **Step 3: SearchPage 集成 SharePanel + CollagePanel**

在 `SearchPage.tsx` 中：

**添加 imports:**
```typescript
import SharePanel from '../components/share/SharePanel';
import CollagePanel from '../components/share/CollagePanel';
```

**添加 states:**
```typescript
const [shareOpen, setShareOpen] = useState(false);
const [collageOpen, setCollageOpen] = useState(false);
const [pendingActionIds, setPendingActionIds] = useState<number[]>([]);
```

**添加 handlers:**
```typescript
  const handleShare = () => {
    const ids = Array.from(selection.selectedIds);
    setPendingActionIds(ids);
    setShareOpen(true);
  };

  const handleCollage = () => {
    const ids = Array.from(selection.selectedIds);
    if (ids.length < 2 || ids.length > 9) {
      alert('拼图需要选择 2-9 张照片');
      return;
    }
    setPendingActionIds(ids);
    setCollageOpen(true);
  };
```

**更新 SelectionActions props**（添加 `onShare` 和 `onCollage`）:
```tsx
<SelectionActions
  onAddToAlbum={handleAddToAlbum}
  onShare={handleShare}
  onCollage={handleCollage}
  onDownload={handleBatchDownload}
  onDelete={handleBatchDelete}
/>
```

**在 JSX 末尾（最外层 `</div>` 之前）添加:**
```tsx
      <SharePanel open={shareOpen} onClose={() => setShareOpen(false)} mediaIds={pendingActionIds} />
      <CollagePanel open={collageOpen} onClose={() => setCollageOpen(false)} mediaIds={pendingActionIds} />
```

- [ ] **Step 4: PeoplePage 集成**

在 `PeoplePage.tsx` 中，同样添加 imports、states、handlers 和 Sheet 组件。与 SearchPage 相同的模式。

**添加 imports:**
```typescript
import SharePanel from '../components/share/SharePanel';
import CollagePanel from '../components/share/CollagePanel';
```

**添加 states:**
```typescript
const [shareOpen, setShareOpen] = useState(false);
const [collageOpen, setCollageOpen] = useState(false);
const [pendingActionIds, setPendingActionIds] = useState<number[]>([]);
```

**添加 handlers:**
```typescript
  const handleShare = () => {
    const ids = Array.from(selection.selectedIds);
    setPendingActionIds(ids);
    setShareOpen(true);
  };

  const handleCollage = () => {
    const ids = Array.from(selection.selectedIds);
    if (ids.length < 2 || ids.length > 9) {
      alert('拼图需要选择 2-9 张照片');
      return;
    }
    setPendingActionIds(ids);
    setCollageOpen(true);
  };
```

**更新 SelectionActions props:**
```tsx
<SelectionActions
  onAddToAlbum={() => {
    const ids = Array.from(selection.selectedIds);
    setPendingAlbumIds(ids);
    setAlbumPickerOpen(true);
  }}
  onShare={handleShare}
  onCollage={handleCollage}
  onDownload={handleBatchDownload}
  onDelete={() => {}}
/>
```

**在 JSX 末尾添加:**
```tsx
      <SharePanel open={shareOpen} onClose={() => setShareOpen(false)} mediaIds={pendingActionIds} />
      <CollagePanel open={collageOpen} onClose={() => setCollageOpen(false)} mediaIds={pendingActionIds} />
```

- [ ] **Step 5: 验证 TypeScript 编译和构建**

```bash
cd frontend && npx tsc --noEmit && npm run build
```

预期: 无错误，构建成功

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/gallery/Lightbox.tsx \
        frontend/src/components/gallery/SelectionActions.tsx \
        frontend/src/pages/SearchPage.tsx \
        frontend/src/pages/PeoplePage.tsx
git commit -m "feat(shares): Lightbox/搜索/人物页集成分享和拼图入口"
```

---

### Task 6: 端到端验证

**Depends on:** Tasks 1-5 all complete

- [ ] **Step 1: 运行后端测试**

```bash
cd backend && python -m pytest tests/ -v
```

预期: 新增 14 个测试（8 shares + 6 collage）全部通过

- [ ] **Step 2: 手动验证分享 API**

```bash
# 启动后端
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8501 &

# 创建分享
curl -s -X POST http://localhost:8501/api/shares \
  -H 'Content-Type: application/json' \
  -d '{"media_ids":[1,2],"title":"测试","expires_in_hours":24}'

# 列表
curl -s http://localhost:8501/api/shares

# 公开查看（用返回的 token 替换）
curl -s http://localhost:8501/api/share/<TOKEN>
```

- [ ] **Step 3: 验证前端构建**

```bash
cd frontend && npm run build
```

预期: 构建成功

- [ ] **Step 4: Commit（如有修正）**

```bash
git add -A
git commit -m "chore: E2E 验证通过 — shares + collage 全部端点 + 前端编译"
```
