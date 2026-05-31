# P2 自动精选集 — 设计文档

**日期:** 2026-06-01  
**状态:** 已确认

## 概述

基于照片质量、人脸和事件参与度自动生成月度精选集。首页展示"本月精选"卡片，独立 CuratedPage 支持按月浏览。

## 后端

### 评分算法

`backend/app/services/curation_service.py`（新建）

```
score = blur_score_normalized × 0.4 + has_face_bonus × 0.3 + event_participation × 0.3
```

- **blur_score_normalized**：`min(blur_score / 1000, 1.0)`，非模糊照片得分高
- **has_face_bonus**：`SELECT COUNT(*) FROM faces WHERE media_id = ?` > 0 → 1，否则 0
- **event_participation**：`event_media_count / MAX(event_media_count)`，归一化

### 数据库

```sql
CREATE TABLE IF NOT EXISTS curated_photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id INTEGER UNIQUE,
    month TEXT NOT NULL,          -- "2026-05"
    score REAL NOT NULL,
    rank INTEGER NOT NULL,
    generated_at TEXT NOT NULL,
    FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE
);
```

### API 端点

文件：`backend/app/routers/admin.py`（追加）

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/admin/curate/generate` | body: `{month?: "2026-05"}` 生成精选集，默认当月 |
| `GET` | `/api/admin/curate` | query: `?month=2026-05` 获取精选结果 |

### 生成逻辑

1. 查询指定月份的所有照片（`date_taken LIKE '2026-05%'`）
2. 对每张计算评分
3. 按 score DESC 排序，取 Top 20
4. 写入 curated_photos 表
5. 返回 `{month, count, items: [...]}`

## 前端

### 新增文件

| 文件 | 说明 |
|------|------|
| `pages/CuratedPage.tsx` | 精选浏览页，按月分组展示 |

### 修改文件

| 文件 | 改动 |
|------|------|
| `App.tsx` | 新增 `/curated` 路由 |
| `api/client.ts` | 新增 curate API 方法 |
| `HomePage.tsx` | 新增"本月精选"section |
| `SettingsPage.tsx` | 新增"生成精选集"按钮 |

### 首页 — 本月精选 Section

- 位置：在"最近收藏"section 之后
- 横向滚动卡片，最多 10 张
- "本月精选"标题 + "查看全部 →"链接到 /curated
- 无数据时不显示（不占空间）

### CuratedPage

- 路由 `/curated`，页面标题 "精选集"
- 按月分组：每个月份一个横向滚动条
- 月份标题：如 "2026年5月 · 20 张精选"
- 点击照片进入 Lightbox

### 设置页

- 在"AI 处理"区域新增"生成精选集"按钮
- 可输入月份（默认当月），点击触发 POST /api/admin/curate/generate

## 不影响

- 现有评分、人脸、事件数据
- 其他所有功能
