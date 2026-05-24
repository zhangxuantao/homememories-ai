# P1 Group A: 重复照片删除 + 收藏功能 + GPU状态展示 设计文档

> **Status:** Approved | **Date:** 2026-05-24 | **Priority:** P0(尾) + P1(首)

## 概述

打包实现三个独立功能：重复照片删除操作（P0 遗留）、收藏功能（P1）、GPU 状态展示（P1）。三者无耦合，可并行实施。

---

## 1. 重复照片删除

### 1.1 现状

- `find_duplicates()` (AI层) 基于 dHash + Hamming 距离 ≤8 检测重复对
- `GET /api/admin/cleanup/duplicates` 返回 `[[MediaItem, MediaItem]]` 配对结果
- `POST /api/admin/cleanup/duplicates/check` 启动后台检测任务
- `DELETE /api/media/{id}` 单个删除端点已存在
- `delete_media()` 删除 DB 记录，不删物理文件
- **缺口：没有批量删除重复的端点，前端无选择/删除交互**

### 1.2 后端设计

#### 新端点: `DELETE /api/admin/cleanup/duplicates`

- **Router:** `backend/app/routers/admin.py`
- **Payload:** `{keep_id: int, delete_ids: list[int]}`
- **行为:** 对 `delete_ids` 逐个调用 `delete_media()`，保留 `keep_id`
- **返回:** `{deleted: N}`

```python
class DeleteDuplicatesRequest(BaseModel):
    keep_id: int
    delete_ids: list[int]

@router.delete("/cleanup/duplicates")
def delete_duplicate_media(body: DeleteDuplicatesRequest):
    conn = get_connection()
    deleted = 0
    for mid in body.delete_ids:
        try:
            delete_media(mid)
            deleted += 1
        except Exception:
            pass
    conn.close()
    return {"deleted": deleted}
```

### 1.3 前端设计

#### 改造 SettingsPage 重复照片区域

**组件复用:** `useSelection` + `SelectionBar` + `SelectionActions`

**交互流程:**
1. 检测完成后，每对显示两张缩略图并排
2. **智能默认选中:** 自动勾选 dHash 质量较差的那张（若可计算），否则不预选
3. 用户点击任一图切换勾选（选中=标记删除，与常规选择逻辑一致）
4. 进入选择模式后，`SelectionActions` 显示"删除选中 (N)"
5. 确认删除后调用 `DELETE /api/admin/cleanup/duplicates`

**关键状态:**
```typescript
const duplicateSelection = useSelection();
const [duplicatePairs, setDuplicatePairs] = useState<[MediaItem, MediaItem][]>([]);
const [deletingIds, setDeletingIds] = useState<Set<number>>(new Set());
```

**删除后处理:** 该对从列表中移除，其他对保留。

---

## 2. 收藏功能

### 2.1 Database

新表：
```sql
CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id INTEGER NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_favorites_created ON favorites(created_at DESC);
```

### 2.2 Backend API

#### `POST /api/favorites/{media_id}` — 切换收藏

```python
@router.post("/api/favorites/{media_id}")
def toggle_favorite(media_id: int):
    # 存在则 DELETE，不存在则 INSERT
    # 返回 {favorited: bool}
```

- 幂等操作：每次调用翻转状态
- 若取消收藏（已存在→删除），返回 `{favorited: false}`
- 若添加收藏（不存在→插入），返回 `{favorited: true}`

#### `GET /api/favorites` — 收藏列表

```python
@router.get("/api/favorites")
def list_favorites(limit: int = 50, offset: int = 0):
    # JOIN media 表返回完整 MediaItem
    # 按 favorites.created_at DESC 排序
```

#### `GET /api/favorites/recent` — 最近收藏

```python
@router.get("/api/favorites/recent")
def recent_favorites(limit: int = 6):
    # 同 list，固定 limit=6，用于首页
```

#### `GET /api/favorites/check` — 批量查询收藏状态（可选优化）

```python
@router.get("/api/favorites/check")
def check_favorites(ids: str = ""):
    # ?ids=1,2,3
    # 返回 {1: true, 2: false, 3: true}
    # 用于 Lightbox 批量查询当前照片是否已收藏
```

**Router 注册:** `backend/app/routers/favorites.py` → 在 `main.py` 注册

### 2.3 Frontend

#### 新建: `frontend/src/hooks/useFavorites.ts`

```typescript
export function useFavorites() {
  // SWR pattern: GET /api/favorites
}

export function useFavoriteStatus(mediaId: number) {
  // GET /api/favorites/check?ids={mediaId}
}

export async function toggleFavorite(mediaId: number): Promise<boolean> {
  // POST /api/favorites/{media_id}
}
```

#### 改造: `frontend/src/components/gallery/Lightbox.tsx`

- 顶栏按钮区插入 ♡/♥ 按钮（在"相似照片"和"下载"之间）
- 未收藏：空心 ♡（`text-white opacity-60`）
- 已收藏：实心 ♥（`text-[#f67280]` 粉红高亮）
- 点击调用 `toggleFavorite(mediaId)`，乐观更新

#### 改造: `frontend/src/pages/HomePage.tsx`

- 新增"最近收藏"section（在"随机回忆"之后，"最近添加"之前）
- 横向滚动条，最多 6 张缩略图
- 右侧"查看全部 →"链接，点击跳转 `/favorites`
- 若无收藏数据，不展示此 section

#### 改造: `frontend/src/components/layout/MobileNav.tsx`

- TABS 数组从 5 项扩到 6 项
- 新增: `{ to: '/favorites', label: '收藏', icon: '❤️' }`
- 放在"搜索"之前（首页 → 时间线 → 收藏 → 搜索 → 人物 → 设置）

#### 新建: `frontend/src/pages/FavoritesPage.tsx`

- 3 列网格（PhotoGrid 复用）
- 支持下拉加载更多（分页）
- 空状态："还没有收藏照片哦～在照片详情页点击 ♡ 即可收藏"
- 长按进入批量选择（复用 `useSelection`），支持取消收藏

#### 改造: `frontend/src/App.tsx`

- 添加 `<Route path="/favorites" element={<FavoritesPage />} />`

### 2.4 前端 API Client 新增

```typescript
// client.ts
toggleFavorite(mediaId: number): Promise<{favorited: boolean}>
getFavorites(limit?: number, offset?: number): Promise<MediaItem[]>
getRecentFavorites(limit?: number): Promise<MediaItem[]>
checkFavorites(ids: number[]): Promise<Record<number, boolean>>
```

---

## 3. GPU 状态展示

### 3.1 Backend

#### 扩展: `GET /api/admin/server-info`

新增 `gpu` 和 `models` 两个子对象：

```python
from app.ai.embedding import embedding_model  # 获取模型状态

info = {
    "hostname": ...,
    "lan_ip": ...,
    "port": 8501,
    "frontend_port": 5173,
    "gpu": {
        "cuda_available": torch.cuda.is_available(),
        "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "device_count": torch.cuda.device_count(),
        "memory_total_gb": round(
            torch.cuda.get_device_properties(0).total_memory / 1e9, 1
        ) if torch.cuda.is_available() else None,
        "memory_used_gb": round(
            torch.cuda.memory_allocated(0) / 1e9, 2
        ) if torch.cuda.is_available() else None,
    },
    "models": {
        "clip_loaded": embedding_model is not None and embedding_model.model is not None,
        "clip_device": str(embedding_model.device) if embedding_model else "not_loaded",
    }
}
```

- 所有 GPU 字段在 `cuda_available=False` 时返回 `None`
- InsightFace 和 FAISS 在需要时可扩展（当前仅 C 端信息展示不需要）
- **容错:** GPU 查询失败不影响其他字段，只返回 `cuda_available: false`

### 3.2 Frontend

#### 更新: `frontend/src/api/client.ts` ServerInfo 接口

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

export interface ServerInfo {
  hostname: string;
  lan_ip: string;
  port: number;
  frontend_port: number;
  gpu: GpuInfo;
  models: ModelInfo;
}
```

#### 改造: `frontend/src/pages/SettingsPage.tsx`

在现有"系统信息"卡片内追加 GPU 子区域：

```
系统信息
├── 媒体数量: 1,234  |  图片: 1,100  |  视频: 134
├── 数据库大小: 45.2 MB
├── 上次扫描: 2026-05-24 14:30
└── [NEW] GPU 状态 ─────────────────────
    ├── 🟢 CUDA 可用: NVIDIA RTX 5080
    ├── 显存: 1.2 GB / 15.8 GB（进度条）
    ├── 🟢 Chinese-CLIP: cuda 模式
    └── [移动端不显示详细GPU信息]
```

- 绿色圆点=cuda 正常，黄色圆点=cpu 降级
- 显存使用率用小进度条展示
- 移动端简化为一行："🟢 GPU: NVIDIA RTX 5080 (1.2/15.8 GB)"

---

## 4. 实施边界

### 不做的
- 收藏不支持分组/标签（那是相册的事）
- 收藏不集成到搜索
- GPU 历史趋势图（P3 统计看板的事）
- InsightFace GPU 加速（P3 事项）
- 删除重复时不删物理文件（延续现有 delete_media 行为）

### 文件清单

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `backend/app/database.py` | 新增 favorites 表 |
| 修改 | `backend/app/routers/admin.py` | 新增 DELETE duplicates 端点 |
| 新建 | `backend/app/routers/favorites.py` | 收藏 CRUD |
| 修改 | `backend/app/main.py` | 注册 favorites router |
| 扩展 | `backend/app/routers/admin.py` (server-info) | GPU + models 字段 |
| 新建 | `frontend/src/hooks/useFavorites.ts` | 收藏 hooks |
| 新建 | `frontend/src/pages/FavoritesPage.tsx` | 收藏独立页 |
| 修改 | `frontend/src/pages/HomePage.tsx` | 新增最近收藏 section |
| 修改 | `frontend/src/pages/SettingsPage.tsx` | 重复删除交互 + GPU 信息 |
| 修改 | `frontend/src/components/gallery/Lightbox.tsx` | 收藏按钮 |
| 修改 | `frontend/src/components/layout/MobileNav.tsx` | 6 tab |
| 修改 | `frontend/src/api/client.ts` | API 拓展 |
| 修改 | `frontend/src/App.tsx` | 收藏路由 |

---

## 5. 测试要点

### 后端
- `DELETE /api/admin/cleanup/duplicates`: 正常删除 / 空列表 / 无效 keep_id
- `POST /api/favorites/{media_id}`: 添加 / 取消 / 不存在的 media_id
- `GET /api/favorites`: 分页 / 空列表 / 与 media 表 JOIN 正确
- `GET /api/admin/server-info`: GPU 可用/不可用的返回值正确

### 前端（手工验证为主，暂无测试框架）
- Lightbox 收藏按钮切换动画
- 首页"最近收藏"在有/无数据时表现正确
- FavoritesPage 空状态 → 收藏一张 → 出现在列表 → 取消收藏 → 消失
- 重复照片删除：勾选 → 删除 → 配对从列表移除
- GPU 信息：设置页显示正确，移动端简洁展示
- 移动端底部导航 6 个 tab 点击正常
