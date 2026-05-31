# P1 外部导入 — 设计文档

**日期:** 2026-05-31  
**状态:** 已确认

## 概述

支持从 Google Takeout zip 和 iCloud 导出目录导入照片到 HomeMemories。照片复制到本地统一管理，导入后自动触发扫描和 AI 处理。

## 后端

文件：`backend/app/routers/import_photos.py`（新建）

### POST /api/import/takeout

- 接收 multipart zip 文件（最大 2GB）
- 解压到临时目录
- 递归查找图片/视频文件（跳过 `*.json` 元数据、`archive_browser.html` 等）
- 复制到 `media_root/imports/takeout_YYYYMMDD_HHMMSS/`
- 清理临时目录，触发 `POST /api/admin/scan` 扫描该子目录
- 返回 `{imported: N, destination: "..."}`

### POST /api/import/icloud

- Body: `{source_dir: "/path/to/icloud_photos"}`
- 验证目录存在且可读
- 递归遍历，复制所有图片/视频到 `media_root/imports/icloud_YYYYMMDD_HHMMSS/`
- 跳过系统文件（`.DS_Store`, `Thumbs.db` 等）
- 触发扫描该子目录
- 返回 `{imported: N, destination: "..."}`

### 支持的格式

与现有上传一致：`.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.tiff`, `.tif`, `.heic`, `.heif`, `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`, `.m4v`

## 前端

### SettingsPage 新增卡片

在设置页 "媒体管理" 卡片下方新增 "外部导入" 卡片：

**Google Takeout 区域：**
- 说明文字："从 Google Takeout 导出的 zip 文件导入照片"
- 文件选择按钮（accept=".zip"）
- 上传进度条
- 完成后显示导入数量 + 目标路径

**iCloud 区域：**
- 说明文字："从 iCloud 导出的照片目录一键迁移"
- 路径输入框 + 浏览按钮（如果可行）
- 导入按钮
- 完成后显示结果

## 数据流

1. 用户选择 zip 或输入目录路径
2. 后端复制文件到 `media_root/imports/` 子目录
3. 调用现有 scan 流程扫描新目录
4. 返回结果，前端显示导入数量和路径

## 不影响

- 现有上传功能（/api/media/upload）
- 现有扫描功能（/api/admin/scan）
- 其他所有功能
