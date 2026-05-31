# 自动精选集 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于多因子评分自动生成月度精选集，首页展示本月精选卡片，独立页面按月浏览。

**Architecture:** 后端新建 curation_service.py 实现评分算法，curated_photos 表存储结果，admin.py 追加 curate 端点。前端新增 CuratedPage，首页和设置页各添加入口。

**Tech Stack:** Python/FastAPI/SQLite 后端 + React/TypeScript 前端

---

### Task 1: 后端 — 评分算法 + curated_photos 表 + API

**Files:**
- Create: `backend/app/services/curation_service.py`
- Modify: `backend/app/database.py`
- Modify: `backend/app/routers/admin.py`
- Create: `backend/tests/test_curation.py`

**Depends on:** Nothing

- [ ] **Step 1: 在 database.py 添加 curated_photos 表**

在 `backend/app/database.py` 的 SCHEMA 末尾（最后的 `"""` 之前）添加：

```sql
CREATE TABLE IF NOT EXISTS curated_photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id INTEGER UNIQUE,
    month TEXT NOT NULL,
    score REAL NOT NULL,
    rank INTEGER NOT NULL,
    generated_at TEXT NOT NULL,
    FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_curated_month ON curated_photos(month);
```

- [ ] **Step 2: 创建 curation_service.py**

```python
# backend/app/services/curation_service.py
from app.database import get_connection


def compute_scores(month: str) -> list[dict]:
    """
    Compute curation scores for all photos in a given month.
    Returns list of {media_id, score} sorted by score DESC.
    """
    conn = get_connection()

    # Get all media for the month
    media = conn.execute(
        "SELECT id, blur_score, is_blurry FROM media "
        "WHERE date_taken LIKE ? AND media_type = 'image'",
        (f"{month}%",),
    ).fetchall()

    if not media:
        conn.close()
        return []

    # Find max event media count for normalization
    max_event_count = conn.execute(
        "SELECT MAX(cnt) FROM ("
        "  SELECT COUNT(*) AS cnt FROM event_media em "
        "  JOIN media m ON em.media_id = m.id "
        "  WHERE m.date_taken LIKE ? "
        "  GROUP BY em.event_id"
        ")",
        (f"{month}%",),
    ).fetchone()[0] or 1

    results = []
    for m in media:
        mid = m["id"]

        # 1. Sharpness score (normalized, 0-1)
        blur = m["blur_score"] or 0
        if m["is_blurry"]:
            sharpness = 0.0
        else:
            sharpness = min(blur / 1000.0, 1.0)

        # 2. Face bonus (1 if has faces, 0 otherwise)
        face_count = conn.execute(
            "SELECT COUNT(*) FROM faces WHERE media_id = ?", (mid,)
        ).fetchone()[0]
        has_face = 1.0 if face_count > 0 else 0.0

        # 3. Event participation (normalized 0-1)
        event_count = conn.execute(
            "SELECT COUNT(*) FROM event_media em "
            "JOIN media m2 ON em.media_id = m2.id "
            "WHERE em.event_id IN ("
            "  SELECT event_id FROM event_media WHERE media_id = ?"
            ")",
            (mid,),
        ).fetchone()[0]
        event_participation = min(event_count / max(max_event_count, 1), 1.0)

        score = sharpness * 0.4 + has_face * 0.3 + event_participation * 0.3
        results.append({"media_id": mid, "score": round(score, 4)})

    conn.close()

    # Sort by score DESC, return top 20
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:20]


def generate_curation(month: str) -> dict:
    """Generate curated collection for a month. Returns summary."""
    from datetime import datetime, timezone

    scores = compute_scores(month)
    if not scores:
        return {"month": month, "count": 0, "items": []}

    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()

    # Clear existing for this month
    conn.execute("DELETE FROM curated_photos WHERE month = ?", (month,))

    for rank, item in enumerate(scores, 1):
        conn.execute(
            "INSERT OR REPLACE INTO curated_photos (media_id, month, score, rank, generated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (item["media_id"], month, item["score"], rank, now),
        )

    conn.commit()
    conn.close()

    return {"month": month, "count": len(scores), "generated_at": now}


def get_curation(month: str) -> dict:
    """Get curated photos for a month."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT cp.*, m.filename, m.thumbnail_path, m.date_taken, "
        "m.width, m.height, m.media_type "
        "FROM curated_photos cp "
        "JOIN media m ON cp.media_id = m.id "
        "WHERE cp.month = ? "
        "ORDER BY cp.rank",
        (month,),
    ).fetchall()
    conn.close()

    return {
        "month": month,
        "items": [
            {
                "id": r["media_id"],
                "score": r["score"],
                "rank": r["rank"],
                "filename": r["filename"],
                "thumbnail_path": r["thumbnail_path"],
                "date_taken": r["date_taken"],
                "width": r["width"],
                "height": r["height"],
                "media_type": r["media_type"],
            }
            for r in rows
        ],
    }
```

- [ ] **Step 3: 在 admin.py 添加 curate 端点**

在 `backend/app/routers/admin.py` 末尾追加：

```python
from pydantic import BaseModel as AdminPydanticModel

class CurateRequest(AdminPydanticModel):
    month: str | None = None  # "2026-05", default = current month


@router.post("/curate/generate")
def generate_curation(body: CurateRequest = None):
    from datetime import datetime
    from app.services.curation_service import generate_curation as do_curate

    if body and body.month:
        month = body.month
    else:
        month = datetime.now().strftime("%Y-%m")

    result = do_curate(month)
    return result


@router.get("/curate")
def get_curation(month: str | None = None):
    from datetime import datetime
    from app.services.curation_service import get_curation as fetch_curation

    if not month:
        month = datetime.now().strftime("%Y-%m")

    return fetch_curation(month)
```

注意：admin.py 中已有一个类似的 Pydantic model（如 ScanRequest 等），请统一导入方式避免重复。如果文件顶部已有 `from pydantic import BaseModel`，就不要新增 `AdminPydanticModel`，直接用已有的 BaseModel 即可。

- [ ] **Step 4: 编写测试**

```python
# backend/tests/test_curation.py
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_connection, init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    db_path = tmp_path / "test_curation.db"
    init_db(db_path)

    from app.database import get_connection as original_get_connection
    def _override():
        return original_get_connection(str(db_path))

    app.dependency_overrides[original_get_connection] = _override

    now = datetime.now()
    month = now.strftime("%Y-%m")

    conn = original_get_connection(str(db_path))
    # Insert test media with varying quality
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_taken, blur_score, is_blurry) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (1, "/test/a.jpg", "a.jpg", "image", f"{month}-01", 800, False),
    )
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_taken, blur_score, is_blurry) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (2, "/test/b.jpg", "b.jpg", "image", f"{month}-15", 200, False),
    )
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_taken, blur_score, is_blurry) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (3, "/test/c.jpg", "c.jpg", "image", f"{month}-20", 100, True),
    )
    # Face for photo 1
    conn.execute(
        "INSERT INTO faces (id, media_id, cluster_id, bbox) VALUES (?, ?, ?, ?)",
        (1, 1, 1, '[0,0,100,100]'),
    )
    conn.commit()
    conn.close()

    yield
    app.dependency_overrides.clear()


def test_generate_curation():
    month = datetime.now().strftime("%Y-%m")
    resp = client.post("/api/admin/curate/generate", json={"month": month})
    assert resp.status_code == 200
    data = resp.json()
    assert data["month"] == month
    assert data["count"] > 0
    assert data["count"] <= 3


def test_get_curation():
    month = datetime.now().strftime("%Y-%m")
    # Generate first
    client.post("/api/admin/curate/generate", json={"month": month})

    resp = client.get(f"/api/admin/curate?month={month}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["month"] == month
    assert len(data["items"]) > 0
    # Highest score should be photo 1 (sharp + has face)
    assert data["items"][0]["id"] == 1


def test_generate_empty_month():
    resp = client.post("/api/admin/curate/generate", json={"month": "2020-01"})
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


def test_get_empty_curation():
    resp = client.get("/api/admin/curate?month=2020-01")
    assert resp.status_code == 200
    assert resp.json()["items"] == []
```

- [ ] **Step 5: 运行测试**

```bash
cd backend && python -m pytest tests/test_curation.py -v
```

预期: 4 tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/curation_service.py backend/app/database.py backend/app/routers/admin.py backend/tests/test_curation.py
git commit -m "feat(curation): 新增自动精选集 — 评分算法 + curated_photos表 + API"
```

---

### Task 2: 前端 — CuratedPage + API 方法

**Files:**
- Modify: `frontend/src/api/client.ts`
- Create: `frontend/src/pages/CuratedPage.tsx`
- Modify: `frontend/src/App.tsx`

**Depends on:** Task 1

- [ ] **Step 1: 在 client.ts 添加 API 方法**

在 `ApiClient` 类的 collage 方法之后添加：

```typescript
  // ── Curation ──

  async generateCuration(month?: string): Promise<{ month: string; count: number }> {
    return this.post<{ month: string; count: number }>('/api/admin/curate/generate', month ? { month } : undefined);
  }

  async getCuration(month?: string): Promise<{ month: string; items: MediaItem[] }> {
    return this.get<{ month: string; items: MediaItem[] }>('/api/admin/curate', { month });
  }
```

- [ ] **Step 2: 创建 CuratedPage**

```typescript
// frontend/src/pages/CuratedPage.tsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { api, type MediaItem } from '../api/client';

interface MonthlyCuration {
  month: string;
  items: MediaItem[];
}

export default function CuratedPage() {
  const navigate = useNavigate();
  const [curations, setCurations] = useState<MonthlyCuration[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch last 6 months
    const months: string[] = [];
    const now = new Date();
    for (let i = 0; i < 6; i++) {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      months.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`);
    }

    Promise.all(months.map(m => api.getCuration(m).catch(() => ({ month: m, items: [] }))))
      .then(results => setCurations(results.filter(c => c.items.length > 0)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (curations.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[80vh] px-6 text-center">
        <span className="text-6xl mb-4">✨</span>
        <p className="text-lg text-text font-semibold mb-2">还没有精选集</p>
        <p className="text-sm text-text-light">去设置页生成精选集吧</p>
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
        ✨ 精选集
      </motion.h1>

      {curations.map(c => (
        <section key={c.month} className="mb-8">
          <h2 className="text-base font-semibold text-text mb-3">
            {c.month.replace('-', '年')}月 · {c.items.length} 张精选
          </h2>
          <div className="flex gap-2 overflow-x-auto scrollbar-none pb-1">
            {c.items.map(item => (
              <div
                key={item.id}
                className="flex-shrink-0 w-24 h-24 rounded-card overflow-hidden bg-misty cursor-pointer hover:opacity-80 transition-opacity"
                onClick={() => navigate(`/photo/${item.id}`, { state: { from: '/curated' } })}
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
      ))}
    </div>
  );
}
```

- [ ] **Step 3: 注册路由**

在 `App.tsx` 中：

```typescript
const CuratedPage = lazy(() => import('./pages/CuratedPage'));
```

添加路由：
```tsx
<Route path="/curated" element={<AnimatedPage><CuratedPage /></AnimatedPage>} />
```

- [ ] **Step 4: 验证 TypeScript**

```bash
cd frontend && npx tsc --noEmit
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/client.ts frontend/src/pages/CuratedPage.tsx frontend/src/App.tsx
git commit -m "feat(curation): 新增 CuratedPage + API 方法"
```

---

### Task 3: 前端 — HomePage 本月精选 + SettingsPage 生成按钮

**Files:**
- Modify: `frontend/src/pages/HomePage.tsx`
- Modify: `frontend/src/pages/SettingsPage.tsx`

**Depends on:** Task 2

- [ ] **Step 1: HomePage 新增"本月精选"section**

在 `HomePage.tsx` 中：

**添加 hook** (在现有 hooks 之后):
```typescript
const [curated, setCurated] = useState<MediaItem[]>([]);
useEffect(() => {
  const month = `${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, '0')}`;
  api.getCuration(month)
    .then(data => setCurated(data.items || []))
    .catch(() => setCurated([]));
}, []);
```

**在"最近收藏"section 之后、"最近添加"section 之前添加:**
```tsx
      {/* 本月精选 */}
      {curated.length > 0 && (
        <section className="mb-8">
          <h2 className="text-base font-semibold text-text mb-3 flex justify-between items-center">
            <span>✨ 本月精选</span>
            <button
              onClick={() => navigate('/curated')}
              className="text-xs text-primary font-normal hover:underline"
            >
              查看全部 →
            </button>
          </h2>
          <div className="flex gap-2 overflow-x-auto scrollbar-none pb-1">
            {curated.slice(0, 10).map((item) => (
              <div
                key={item.id}
                className="flex-shrink-0 w-24 h-24 rounded-card overflow-hidden bg-misty cursor-pointer hover:opacity-80 transition-opacity"
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

- [ ] **Step 2: SettingsPage 新增"生成精选集"按钮**

在 `frontend/src/pages/SettingsPage.tsx` 中，找到"AI 处理"Section（`<Section title="AI 处理">`），在现有按钮（如人脸检测、人脸聚类）之后添加：

```tsx
          <ActionButton
            label="生成精选集"
            onClick={async () => {
              setJobStatus({ status: 'running', progress: 0, job_id: '', error: null });
              try {
                const result = await api.generateCuration();
                alert(`精选集生成完成！${result.month} 月共 ${result.count} 张精选照片`);
                setJobStatus({ status: 'completed', progress: 100, job_id: '', error: null });
              } catch (err) {
                alert('生成失败: ' + (err as Error).message);
                setJobStatus({ status: 'failed', progress: 0, job_id: '', error: (err as Error).message });
              }
            }}
          />
```

- [ ] **Step 3: 验证 TypeScript 编译和构建**

```bash
cd frontend && npx tsc --noEmit && npm run build
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/HomePage.tsx frontend/src/pages/SettingsPage.tsx
git commit -m "feat(curation): 首页本月精选 + 设置页生成按钮"
```

---

### Task 4: 端到端验证

**Depends on:** Tasks 1-3

- [ ] **Step 1: 运行后端测试**

```bash
cd backend && python -m pytest tests/test_curation.py -v
```

预期: 4 tests PASS

- [ ] **Step 2: 验证前端构建**

```bash
cd frontend && npm run build
```

预期: 构建成功

- [ ] **Step 3: Commit（如有修正）**
