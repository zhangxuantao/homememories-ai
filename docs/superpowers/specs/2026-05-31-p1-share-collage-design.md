# P1 分享/导出 — 设计文档

**日期:** 2026-05-31  
**状态:** 已确认

## 概述

实现局域网分享链接和拼图功能。zip 导出已在前序迭代中实现。

## 现状

- `/api/media/export-zip` 已完成，前端 SearchPage/PeoplePage 已集成批量下载
- Lightbox 已有单张下载
- 分享和拼图为零实现

## 分享系统

### 数据库

```sql
CREATE TABLE IF NOT EXISTS shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT UNIQUE NOT NULL,
    title TEXT,
    media_ids TEXT NOT NULL,          -- JSON array: [1, 2, 3]
    expires_at TEXT,                   -- NULL = 永不过期
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL
);
```

### 后端端点

文件：`backend/app/routers/shares.py`（新建）

**认证端点：**

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/shares` | 创建分享，body: `{media_ids, title?, expires_in_hours?}` |
| `GET` | `/api/shares` | 列出所有分享，按 created_at DESC |
| `DELETE` | `/api/shares/{id}` | 撤销分享，设 is_active=0 |

**公开端点（无需认证）：**

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/share/{token}` | 获取分享：验证有效性+未过期，返回 media 列表 |

### 分享逻辑

- 创建时生成 16 位随机 token（urlsafe base64）
- 过期检查：`expires_at IS NULL OR expires_at > now()`
- 撤销 = 设置 is_active=0（软删除，不删记录）
- 公开端点不含服务器信息，仅返回照片数据

## 拼图系统

### 后端端点

文件：`backend/app/routers/media.py`（追加）

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/media/collage` | body: `{media_ids, layout}` → PNG 图片流 |

### 布局规则

- **grid**（默认）：尽量正方形排列（2→1x2, 3→1x3 或 2x2缺1, 4→2x2, 5→2x3缺1, 6→2x3, 7-9→3x3）
- **horizontal**：横向拼接，所有图片缩放到同高
- **vertical**：纵向拼接，所有图片缩放到同宽

每张缩略图缩放到 400px，最终拼图 JPEG 质量 90。

## 前端

### 新增文件

| 文件 | 说明 |
|------|------|
| `pages/ShareViewPage.tsx` | 公开分享查看页 — 网格展示 + Lightbox |
| `components/share/SharePanel.tsx` | 底部 Sheet — 创建分享（标题/有效期/复制链接） |
| `components/share/CollagePanel.tsx` | 底部 Sheet — 拼图布局选择 + 预览下载 |

### 修改文件

| 文件 | 改动 |
|------|------|
| `App.tsx` | 新增 `/share/:token` 路由 |
| `api/client.ts` | 新增 shares + collage API 方法 |
| `Lightbox.tsx` | 顶栏加分享按钮 |
| `SelectionActions.tsx` | 加分享、拼图按钮 |
| `SearchPage.tsx` | 集成 SharePanel + CollagePanel |
| `PeoplePage.tsx` | 同上 |

### ShareViewPage

- 路由 `/share/:token`，无需导航栏（无 MobileNav/DesktopRail）
- 照片网格展示（复用 PhotoGrid），点击进入简易 Lightbox
- 顶部显示标题 + 过期时间
- token 无效/过期时显示错误提示
- 空状态：404 样式

### SharePanel

- 底部 Sheet，标题 "分享照片 (N张)"
- 已选照片缩略图横向滚动条
- 标题输入框（可选）
- 有效期选择器：1小时 / 24小时 / 7天 / 永久（分段按钮）
- 创建按钮 → 生成链接
- 生成后显示：链接文本框 + 复制按钮 + toast "已复制"
- 关闭按钮

### CollagePanel

- 底部 Sheet，标题 "拼图 (N张)"
- 布局选择：网格 / 横向 / 纵向（三选一分段按钮）
- 预览缩略图
- 下载按钮 → POST /api/media/collage → blob → download
- 最多 9 张

## 不影响

- 现有导出的 zip 功能
- 收藏、相册、搜索、设置
- 导航结构
