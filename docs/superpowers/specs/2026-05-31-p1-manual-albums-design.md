# P1 手动相册 — 设计文档

**日期:** 2026-05-31  
**状态:** 已确认

## 概述

实现手动相册功能：用户可创建/命名/换封面/删除相册，将照片归入相册。与 AI 事件互补，提供用户主动组织照片的方式。

## 现状

- 数据库已有 `albums` 和 `album_media` 表（Phase 2 时创建）
- 后端 `albums.py` 已有基础 CRUD：list/create/add media/get media/remove media
- 前端零实现：无页面、无路由、无组件
- SearchPage 中"加入相册"使用 `prompt()` 直接调 API，体验差

## 后端改动

文件：`backend/app/routers/albums.py`

新增 3 个端点：

### GET /{album_id}
返回相册详情（id, name, cover_media_id, cover_thumbnail, media_count, created_at, updated_at）

### PATCH /{album_id}
Body: `{name?: string, cover_media_id?: int}`  
重命名或更换封面（从相册内已有照片中选）

### DELETE /{album_id}
删除相册，`album_media` 记录由 FK CASCADE 自动清理

## 前端改动

### 新增文件

| 文件 | 说明 |
|------|------|
| `pages/AlbumsPage.tsx` | 相册列表页 — 卡片网格，创建/重命名/删除 |
| `pages/AlbumDetailPage.tsx` | 相册详情页 — 封面Hero + 瀑布流网格 + 批量操作 |
| `components/albums/AlbumPickerSheet.tsx` | 底部弹出Sheet — 选相册或新建，可在任何页面调用 |

### 修改文件

| 文件 | 改动 |
|------|------|
| `App.tsx` | 新增 `/albums` 和 `/albums/:id` 路由 |
| `api/client.ts` | 新增 albums API 方法（list/create/get/patch/delete/addMedia/removeMedia） |
| `MobileNav.tsx` | 第6个tab "设置⚙️" → "相册📁" |
| `DesktopRail.tsx` | 同上 |
| `HomePage.tsx` | 右上角添加齿轮图标链接到 `/settings` |
| `SearchPage.tsx` | "加入相册"按钮触发 AlbumPickerSheet |
| `PeoplePage.tsx` | 同上 |

### AlbumpsPage 设计

- 2列卡片网格（md+ 3-4列），卡片: 封面缩略图 + 相册名 + 照片数量
- 右上角 "+" 按钮 → 输入框创建新相册
- 空状态：引导文案
- 长按/右键卡片：操作菜单（重命名/删除），删除需确认
- 排序：按 `updated_at DESC`

### AlbumDetailPage 设计

- 顶部 Hero：封面大图（模糊背景），相册名，数量，操作按钮（添加照片/编辑/删除）
- 瀑布流网格：CSS columns masonry 布局
- 批量选择：复用 `useSelection` hook，移除/下载
- 空状态：引导添加照片
- 左上角返回箭头

### AlbumPickerSheet 设计

- 底部滑出半屏面板
- 顶部输入框：输入名称 → 回车创建并添加；下方相册列表
- 相册列表项：封面缩略图 + 名称 + 数量
- 点击相册 → POST 添加选中照片 → toast → 关闭

### 导航设计

- MobileNav: 6 tab grid，第6项从"设置⚙️"改为"相册📁"
- DesktopRail: 同步替换
- 设置入口：首页右上角 `<Link to="/settings">` 齿轮图标

### 数据流

- AlbumsPage 挂载 → GET /api/albums → 渲染卡片网格
- 创建相册 → POST /api/albums → 刷新列表
- 重命名 → PATCH /api/albums/:id {name} → 刷新
- 删除 → DELETE /api/albums/:id → 刷新
- AlbumDetailPage 挂载 → GET /api/albums/:id + GET /api/albums/:id/media → 渲染
- AlbumPickerSheet → GET /api/albums → 选相册 → POST /api/albums/:id/media

## 不影响

- 现有 AI 事件系统
- 收藏功能
- 人物相册
- 搜索和清理功能
