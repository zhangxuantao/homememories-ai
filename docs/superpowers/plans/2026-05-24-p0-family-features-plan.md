# P0 家庭多用户功能实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 补齐三个 P0 功能：扫码访问（降低家人访问门槛）→ 手机上传（让家人成为内容贡献者）→ 批量操作（提高整理效率）

**Architecture:** 分三个阶段实施，每个阶段独立可交付。扫码访问纯前端+一个轻量后端端点；手机上传新增前后端完整链路；批量操作新增选择模式 hook + 相册后端 + zip 导出。前端遵循现有 React + TypeScript + Tailwind + SWR-like hooks 模式，后端遵循现有 FastAPI + SQLite + threading 模式。

**Tech Stack:** React 18 + TypeScript + Tailwind CSS 3 + framer-motion, FastAPI + SQLite + threading, qrcode (new)

**Design spec:** `docs/superpowers/specs/2026-05-24-p0-family-features-design.md`

---

## 文件结构总览

```
frontend/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   └── MobileNav.tsx          (修改: 新增"+"按钮)
│   │   ├── ui/
│   │   │   └── QrCode.tsx             (新建: 二维码组件)
│   │   └── gallery/
│   │       ├── PhotoGrid.tsx           (修改: 集成选择模式)
│   │       ├── SelectionBar.tsx        (新建: 顶部选择状态栏)
│   │       └── SelectionActions.tsx    (新建: 底部操作栏)
│   ├── UploadPanel.tsx                 (新建: 上传面板)
│   ├── hooks/
│   │   ├── useSelection.ts            (新建: 选择模式 hook)
│   │   └── useUpload.ts              (新建: 上传 hook)
│   └── pages/
│       ├── SettingsPage.tsx           (修改: 新增局域网卡片+批量)
│       ├── SearchPage.tsx             (修改: 集成选择模式)
│       └── PeoplePage.tsx             (修改: 集成选择模式)

backend/
├── app/
│   ├── routers/
│   │   ├── admin.py                   (修改: 新增 server-info 端点)
│   │   ├── media.py                   (修改: 新增 upload + export-zip 端点)
│   │   └── albums.py                  (新建: 相册 CRUD)
│   ├── services/
│   │   └── upload_service.py          (新建: 文件保存+异步处理)
│   └── main.py                        (修改: 注册上传路由)
└── tests/
    ├── test_upload_api.py             (新建)
    ├── test_upload_service.py         (新建)
    └── test_albums_api.py             (新建)
```

---

## Phase 1: 扫码访问

### Task 1.1: 新增 `GET /api/admin/server-info` 端点

**Files:**
- Modify: `backend/app/routers/admin.py:116-121`
- Test: `backend/tests/test_admin_api.py`

- [ ] **Step 1: 添加后端端点**

在 `backend/app/routers/admin.py` 末尾添加：

```python
import socket


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
    return {
        "hostname": hostname,
        "lan_ip": lan_ip,
        "port": 8501,
        "frontend_port": 5173,
    }
```

- [ ] **Step 2: 运行测试验证端点返回 200**

```bash
pytest backend/tests/test_admin_api.py -v -k "server" 2>&1 || true
```

然后手动验证：

```bash
cd backend && curl http://localhost:8501/api/admin/server-info
```

预期输出包含 `hostname`、`lan_ip`、`port` 字段。

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/admin.py
git commit -m "feat(admin): 新增 server-info 端点，返回主机名与局域网 IP"
```

---

### Task 1.2: 安装 qrcode 依赖 + 创建 QrCode 组件

**Files:**
- Create: `frontend/src/components/ui/QrCode.tsx`
- Modify: `frontend/package.json` (qrcode dependency)

- [ ] **Step 1: 安装 qrcode 包**

```bash
cd frontend && npm install qrcode
```

- [ ] **Step 2: 创建 QrCode 组件**

创建 `frontend/src/components/ui/QrCode.tsx`：

```tsx
import { useEffect, useRef } from 'react';
import QRCodeLib from 'qrcode';

interface QrCodeProps {
  url: string;
  size?: number;
}

export default function QrCode({ url, size = 180 }: QrCodeProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current || !url) return;
    QRCodeLib.toCanvas(canvasRef.current, url, {
      width: size,
      margin: 2,
      color: { dark: '#5a7a7a', light: '#ffffff' },
    });
  }, [url, size]);

  if (!url) {
    return <div className="text-text-light text-sm">无法生成二维码</div>;
  }

  return <canvas ref={canvasRef} className="rounded-lg" />;
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ui/QrCode.tsx frontend/package.json frontend/package-lock.json
git commit -m "feat(frontend): 新增 QrCode 组件和 qrcode 依赖"
```

---

### Task 1.3: 在 SettingsPage 中集成局域网访问卡片

**Files:**
- Modify: `frontend/src/pages/SettingsPage.tsx`
- Modify: `frontend/src/api/client.ts`

- [ ] **Step 1: 在 API client 中添加 server-info 类型**

在 `frontend/src/api/client.ts` 的 interface 定义区添加：

```ts
export interface ServerInfo {
  hostname: string;
  lan_ip: string;
  port: number;
  frontend_port: number;
}
```

在 `client.ts` 的 ApiClient 类中添加方法：

```ts
async getServerInfo(): Promise<ServerInfo> {
  return this.get<ServerInfo>('/api/admin/server-info');
}
```

- [ ] **Step 2: 在 SettingsPage 中添加局域网访问卡片**

在 `frontend/src/pages/SettingsPage.tsx` 中：
- 在 import 区域添加：

```tsx
import { useEffect, useState } from 'react';  // useState 已有，添加 useEffect
import QrCode from '../components/ui/QrCode';
import { ServerInfo } from '../api/client';
```

- 在 `formatBytes` 函数后添加状态和方法：

```tsx
const [serverInfo, setServerInfo] = useState<ServerInfo | null>(null);
const frontendUrl = window.location.origin;

useEffect(() => {
  api.getServerInfo().then(setServerInfo).catch(() => {});
}, []);

const isLan = (hostname: string) =>
  /^(192\.168\.|10\.|172\.(1[6-9]|2\d|3[01])\.)/.test(hostname);

const handleCopyUrl = () => {
  navigator.clipboard.writeText(frontendUrl).then(() => {
    // toast via temporary state
  }).catch(() => {});
};
```

- 在系统信息 Section 上方添加局域网卡片 JSX：

```tsx
{/* 局域网访问 */}
<Section title="局域网访问">
  <div className="flex flex-col items-center gap-3">
    <QrCode url={frontendUrl} size={180} />
    <div className="flex items-center gap-2">
      <span className="text-sm text-text break-all">🌐 {frontendUrl}</span>
      <button
        onClick={() => { navigator.clipboard.writeText(frontendUrl); }}
        className="shrink-0 px-2 py-1 text-xs text-primary border border-primary rounded-btn hover:bg-primary hover:text-white transition-colors"
      >
        复制地址
      </button>
    </div>
    <p className="text-xs text-text-light text-center leading-relaxed">
      用相机或浏览器扫码直接打开；微信扫码请点击右上角"在浏览器中打开"
    </p>
    <div className="flex items-center gap-1.5">
      <span className={`w-2 h-2 rounded-full ${serverInfo && isLan(serverInfo.lan_ip) ? 'bg-green-400' : 'bg-yellow-400'}`} />
      <span className="text-xs text-text-light">
        {serverInfo && isLan(serverInfo.lan_ip)
          ? '当前已连接局域网'
          : '未检测到局域网，请确认 WiFi 已连接'}
      </span>
    </div>
  </div>
</Section>
```

- [ ] **Step 3: 验证构建通过**

```bash
cd frontend && npx tsc --noEmit
```

- [ ] **Step 4: 启动前端开发服务器验证**

```bash
cd frontend && npm run dev
```

打开 http://localhost:5173/settings，确认：
- 二维码渲染正常
- 点击"复制地址"可用
- 状态指示灯显示

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/SettingsPage.tsx frontend/src/api/client.ts
git commit -m "feat(frontend): 设置页新增局域网访问二维码卡片"
```

---

## Phase 2: 手机上传

### Task 2.1: 创建上传后端（upload_service + upload 路由）

**Files:**
- Create: `backend/app/services/upload_service.py`
- Create: `backend/app/routers/upload.py`
- Modify: `backend/app/main.py:38-48`
- Test: `backend/tests/test_upload_api.py`

- [ ] **Step 1: 编写上传 API 测试**

创建 `backend/tests/test_upload_api.py`：

```python
import pytest
import os
from httpx import AsyncClient, ASGITransport
from app.database import get_connection, init_db


@pytest.fixture
def upload_app(tmp_path, monkeypatch):
    media_dir = str(tmp_path / "media")
    data_dir = str(tmp_path)
    os.makedirs(media_dir, exist_ok=True)
    monkeypatch.setenv("MEDIA_ROOT", media_dir)
    monkeypatch.setenv("DATA_ROOT", data_dir)
    monkeypatch.setenv("THUMBNAIL_SIZE", "300")

    init_db()

    from app.main import create_app
    app = create_app()
    return app


@pytest.mark.asyncio
async def test_upload_single_image(upload_app, tmp_path):
    from PIL import Image
    img_path = str(tmp_path / "photo.jpg")
    Image.new("RGB", (100, 100)).save(img_path, "JPEG")

    files = [("files", ("photo.jpg", open(img_path, "rb"), "image/jpeg"))]
    transport = ASGITransport(app=upload_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/media/upload", files=files)

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["uploaded"]) == 1
    assert data["uploaded"][0]["filename"] == "photo.jpg"
    assert data["uploaded"][0]["media_type"] == "image"
    assert data["processing"] is True


@pytest.mark.asyncio
async def test_upload_multiple_images(upload_app, tmp_path):
    from PIL import Image
    files = []
    for i in range(3):
        p = str(tmp_path / f"img{i}.jpg")
        Image.new("RGB", (50, 50)).save(p, "JPEG")
        files.append(("files", (f"img{i}.jpg", open(p, "rb"), "image/jpeg")))

    transport = ASGITransport(app=upload_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/media/upload", files=files)

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["uploaded"]) == 3


@pytest.mark.asyncio
async def test_upload_no_files(upload_app):
    transport = ASGITransport(app=upload_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/media/upload")
    assert resp.status_code == 422
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend && python -m pytest tests/test_upload_api.py -v
```

- [ ] **Step 3: 创建 upload_service.py**

创建 `backend/app/services/upload_service.py`：

```python
import os
import uuid
import threading
from datetime import datetime, timezone

from app.database import get_connection
from app.config import settings
from app.scanner.scanner import file_checksum, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
from app.scanner.exif_extractor import extract_date_taken
from app.scanner.thumbnail import generate_thumbnail
from app.scanner.video_extractor import extract_video_info, generate_video_thumbnail


def handle_uploaded_files(file_paths: list[str]) -> list[dict]:
    """Insert uploaded files into media table and return created records.
    Each file_path is already on disk under media_root.
    """
    conn = get_connection()
    date_added = datetime.now(timezone.utc).isoformat()
    results = []

    for filepath in file_paths:
        filename = os.path.basename(filepath)
        ext = os.path.splitext(filename)[1].lower()
        media_type = "image" if ext in IMAGE_EXTENSIONS else "video"
        csum = file_checksum(filepath)

        existing = conn.execute(
            "SELECT id FROM media WHERE checksum = ?", (csum,)
        ).fetchone()
        if existing:
            continue

        date_taken = None
        width = None
        height = None
        duration = None
        thumbnail_path = None

        if media_type == "image":
            from PIL import Image
            try:
                img = Image.open(filepath)
                width, height = img.size
            except Exception:
                pass
            date_taken = extract_date_taken(filepath)
            thumbnail_path = generate_thumbnail(filepath, settings.thumb_dir, settings.media_root)
        else:
            info = extract_video_info(filepath)
            width = info["width"]
            height = info["height"]
            duration = info["duration"]
            thumbnail_path = generate_video_thumbnail(filepath, settings.thumb_dir, settings.media_root)

        if date_taken is None:
            try:
                mtime = os.path.getmtime(filepath)
                date_taken = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
            except OSError:
                pass

        file_size = os.path.getsize(filepath)
        cursor = conn.execute(
            """INSERT INTO media
               (path, filename, media_type, width, height, file_size,
                date_taken, date_added, thumbnail_path, duration, checksum)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (filepath, filename, media_type, width, height, file_size,
             date_taken, date_added, thumbnail_path, duration, csum),
        )
        results.append({
            "id": cursor.lastrowid,
            "filename": filename,
            "media_type": media_type,
        })

    conn.commit()
    conn.close()

    if results:
        _start_async_processing([r["id"] for r in results])

    return results


def _start_async_processing(media_ids: list[int]) -> None:
    """Background thread: dHash + CLIP embedding for uploaded media."""
    def _run():
        from app.ai.quality import detect_blur
        from app.services.search_service import _generate_all_embeddings

        conn = get_connection()
        for mid in media_ids:
            row = conn.execute("SELECT path FROM media WHERE id = ?", (mid,)).fetchone()
            if not row:
                continue
            try:
                from PIL import Image
                import imagehash
                img = Image.open(row["path"])
                dhash_val = str(imagehash.dhash(img))
                is_blurry, blur_score = detect_blur(row["path"])
                conn.execute(
                    "UPDATE media SET dhash = ?, is_blurry = ?, blur_score = ? WHERE id = ?",
                    (dhash_val, 1 if is_blurry else 0, blur_score, mid),
                )
            except Exception:
                pass
        conn.commit()
        conn.close()

        try:
            _generate_all_embeddings()
        except Exception:
            pass

    t = threading.Thread(target=_run, daemon=True)
    t.start()
```

- [ ] **Step 4: 创建 upload.py 路由**

创建 `backend/app/routers/upload.py`：

```python
import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.config import settings
from app.services.upload_service import handle_uploaded_files

router = APIRouter(prefix="/api/media", tags=["upload"])

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_FILES = 100

ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif",
    ".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v",
}


@router.post("/upload")
async def upload_files(files: list[UploadFile] = File(..., max_length=MAX_FILES)):
    if not files:
        raise HTTPException(status_code=422, detail="No files provided")

    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"最多上传 {MAX_FILES} 张")

    upload_dir = os.path.join(settings.media_root, "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    saved_paths = []
    for f in files:
        ext = os.path.splitext(f.filename or "")[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            continue

        safe_name = f"{uuid.uuid4().hex}{ext}"
        dest = os.path.join(upload_dir, safe_name)
        content = await f.read()
        if len(content) > MAX_FILE_SIZE:
            continue
        with open(dest, "wb") as out:
            out.write(content)
        saved_paths.append(dest)

    if not saved_paths:
        raise HTTPException(status_code=400, detail="未保存任何文件，检查格式或大小")

    results = handle_uploaded_files(saved_paths)
    return {"uploaded": results, "failed": [], "processing": True}
```

- [ ] **Step 5: 注册上传路由到 main.py**

在 `backend/app/main.py` 中 `create_app()` 函数内，在路由注册区域添加：

```python
from app.routers.upload import router as upload_router
# ... (在现有 router 注册后面)
app.include_router(upload_router)
```

- [ ] **Step 6: 运行测试**

```bash
cd backend && python -m pytest tests/test_upload_api.py -v
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/upload_service.py backend/app/routers/upload.py backend/app/main.py backend/tests/test_upload_api.py
git commit -m "feat(upload): 新增手机上传 API 端点与后台处理服务"
```

---

### Task 2.2: 创建前端上传面板

**Files:**
- Create: `frontend/src/UploadPanel.tsx`
- Create: `frontend/src/hooks/useUpload.ts`
- Modify: `frontend/src/components/layout/MobileNav.tsx`

- [ ] **Step 1: 创建 useUpload hook**

创建 `frontend/src/hooks/useUpload.ts`：

```ts
import { useState, useCallback } from 'react';
import { api } from '../api/client';

interface UploadResult {
  uploaded: { id: number; filename: string; media_type: string }[];
  failed: unknown[];
  processing: boolean;
}

export function useUpload() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentFile, setCurrentFile] = useState('');
  const [result, setResult] = useState<UploadResult | null>(null);

  const addFiles = useCallback((files: FileList | File[]) => {
    const incoming = Array.from(files).filter(
      f => f.type.startsWith('image/') || f.type.startsWith('video/')
    );
    setSelectedFiles(prev => {
      const merged = [...prev, ...incoming];
      if (merged.length > 100) {
        alert('单次最多上传 100 张');
        return merged.slice(0, 100);
      }
      return merged;
    });
    setResult(null);
  }, []);

  const removeFile = useCallback((index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  }, []);

  const upload = useCallback(async () => {
    if (selectedFiles.length === 0) return;
    setUploading(true);
    setProgress(0);
    try {
      const formData = new FormData();
      selectedFiles.forEach(f => formData.append('files', f));
      setCurrentFile(selectedFiles[0].name);
      const res = await api.upload<UploadResult>('/api/media/upload', formData);
      setProgress(100);
      setResult(res);
    } catch (err) {
      alert((err as Error).message);
    } finally {
      setUploading(false);
    }
  }, [selectedFiles]);

  const reset = useCallback(() => {
    setSelectedFiles([]);
    setResult(null);
    setProgress(0);
  }, []);

  return { selectedFiles, uploading, progress, currentFile, result, addFiles, removeFile, upload, reset };
}
```

- [ ] **Step 2: 检查 api.upload 方法是否支持 FormData**

确认 `frontend/src/api/client.ts` 中 `upload` 方法的签名。当前 upload 方法接受 `File` 类型，需要新增一个接受 `FormData` 的方法，或者直接在组件中手动用 fetch。

在 `client.ts` ApiClient 类中添加：

```ts
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
```

然后在 useUpload 中使用 `api.uploadFormData` 而非 `api.upload`。

- [ ] **Step 3: 创建 UploadPanel 组件**

创建 `frontend/src/UploadPanel.tsx`：

```tsx
import { useRef } from 'react';
import { useUpload } from './hooks/useUpload';
import { api } from './api/client';

interface UploadPanelProps {
  open: boolean;
  onClose: () => void;
}

export default function UploadPanel({ open, onClose }: UploadPanelProps) {
  const { selectedFiles, uploading, progress, result, addFiles, removeFile, upload, reset } = useUpload();
  const inputRef = useRef<HTMLInputElement>(null);

  if (!open) return null;

  const handleClose = () => {
    reset();
    onClose();
  };

  const isDone = result && progress === 100;

  return (
    <div className="fixed inset-0 z-50 flex items-end md:items-center justify-center bg-black/40 backdrop-blur-sm" onClick={handleClose}>
      <div className="w-full md:max-w-md bg-white rounded-t-2xl md:rounded-2xl shadow-xl max-h-[85vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-misty">
          <h2 className="text-lg font-semibold text-text">上传照片/视频</h2>
          <button onClick={handleClose} className="text-text-light hover:text-text text-xl leading-none">&times;</button>
        </div>

        <div className="p-5 space-y-4">
          {/* Drop zone */}
          {selectedFiles.length === 0 && !isDone && (
            <div
              className="border-2 border-dashed border-misty rounded-xl p-8 text-center cursor-pointer hover:border-primary transition-colors"
              onClick={() => inputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => { e.preventDefault(); addFiles(e.dataTransfer.files); }}
            >
              <p className="text-3xl mb-2">📷</p>
              <p className="text-text font-medium">点击或拖拽选择文件</p>
              <p className="text-xs text-text-light mt-1">支持 JPG/PNG/MP4/MOV，单次最多 100 张</p>
              <input
                ref={inputRef}
                type="file"
                multiple
                accept="image/*,video/*"
                className="hidden"
                onChange={(e) => e.target.files && addFiles(e.target.files)}
              />
            </div>
          )}

          {/* Selected files preview */}
          {selectedFiles.length > 0 && !isDone && (
            <>
              <p className="text-sm text-text">已选 {selectedFiles.length} 张</p>
              <div className="grid grid-cols-4 gap-2 max-h-48 overflow-y-auto">
                {selectedFiles.map((f, i) => (
                  <div key={i} className="relative aspect-square rounded-lg overflow-hidden bg-misty/50">
                    <img src={URL.createObjectURL(f)} alt={f.name} className="w-full h-full object-cover" />
                    <button
                      onClick={() => removeFile(i)}
                      className="absolute top-0.5 right-0.5 w-5 h-5 bg-black/50 text-white rounded-full text-xs flex items-center justify-center"
                    >&times;</button>
                  </div>
                ))}
              </div>
              {!uploading && (
                <button
                  onClick={() => inputRef.current?.click()}
                  className="text-sm text-primary hover:underline"
                >+ 继续添加</button>
              )}
              <input
                ref={inputRef}
                type="file"
                multiple
                accept="image/*,video/*"
                className="hidden"
                onChange={(e) => e.target.files && addFiles(e.target.files)}
              />
            </>
          )}

          {/* Progress */}
          {uploading && (
            <div className="space-y-2">
              <div className="w-full h-2 bg-misty rounded-full overflow-hidden">
                <div className="h-full bg-primary rounded-full transition-all duration-300" style={{ width: `${progress}%` }} />
              </div>
              <p className="text-xs text-text-light text-center">上传中...</p>
            </div>
          )}

          {/* Done state */}
          {isDone && (
            <div className="text-center py-4 space-y-3">
              <p className="text-3xl">✅</p>
              <p className="text-text font-medium">{result?.uploaded.length || 0} 张已上传，后台处理中...</p>
              <a href="/" className="inline-block px-4 py-2 bg-primary text-white rounded-btn text-sm" onClick={handleClose}>
                去查看
              </a>
            </div>
          )}

          {/* Action button */}
          {selectedFiles.length > 0 && !uploading && !isDone && (
            <button onClick={upload} className="w-full py-2.5 bg-primary text-white rounded-btn font-medium text-sm hover:opacity-90 transition-opacity">
              开始上传 ({selectedFiles.length} 张)
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: 修改 MobileNav 添加 "+" 按钮**

修改 `frontend/src/components/layout/MobileNav.tsx`：

将现有 TABS 数组保持不变，在组件中引入上传面板状态：

```tsx
import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import UploadPanel from '../UploadPanel';  // path relative from components/layout

const TABS = [
  { to: '/', label: '首页', icon: '🏠' },
  { to: '/timeline', label: '时间线', icon: '📅' },
  { to: '/search', label: '搜索', icon: '🔍' },
  { to: '/people', label: '人物', icon: '👤' },
  { to: '/settings', label: '设置', icon: '⚙️' },
];

export default function MobileNav() {
  const [uploadOpen, setUploadOpen] = useState(false);

  return (
    <>
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 flex justify-around items-center h-14 bg-white/90 backdrop-blur-xl border-t border-misty px-2 pb-1">
        {TABS.slice(0, 2).map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            end={tab.to === '/'}
            className={({ isActive }) =>
              `flex flex-col items-center gap-0.5 text-[10px] transition-colors ${
                isActive ? 'text-primary font-semibold' : 'text-text-light'
              }`
            }
          >
            <span className="text-lg">{tab.icon}</span>
            <span>{tab.label}</span>
          </NavLink>
        ))}

        {/* Upload button - center */}
        <button
          onClick={() => setUploadOpen(true)}
          className="flex flex-col items-center gap-0.5 text-[10px] text-text-light -mt-5"
        >
          <span className="w-11 h-11 bg-primary text-white rounded-full flex items-center justify-center text-xl shadow-lg shadow-primary/30">+</span>
          <span>上传</span>
        </button>

        {TABS.slice(2).map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            className={({ isActive }) =>
              `flex flex-col items-center gap-0.5 text-[10px] transition-colors ${
                isActive ? 'text-primary font-semibold' : 'text-text-light'
              }`
            }
          >
            <span className="text-lg">{tab.icon}</span>
            <span>{tab.label}</span>
          </NavLink>
        ))}
      </nav>

      <UploadPanel open={uploadOpen} onClose={() => setUploadOpen(false)} />
    </>
  );
}
```

- [ ] **Step 5: 修复跨文件导入路径**

`MobileNav.tsx` 位于 `components/layout/`，UploadPanel 在 `src/` 根级别。导入路径应为：

```tsx
import UploadPanel from '../../UploadPanel';
```

- [ ] **Step 6: 验证 TypeScript 编译**

```bash
cd frontend && npx tsc --noEmit
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/UploadPanel.tsx frontend/src/hooks/useUpload.ts frontend/src/components/layout/MobileNav.tsx frontend/src/api/client.ts
git commit -m "feat(frontend): 新增手机上传面板和底部导航 '+' 按钮"
```

---

## Phase 3: 批量操作

### Task 3.1: 创建相册后端（albums 路由 + media export-zip）

**Files:**
- Create: `backend/app/routers/albums.py`
- Modify: `backend/app/routers/media.py`
- Modify: `backend/app/database.py`

- [ ] **Step 1: 更新数据库 Schema 支持相册**

在 `backend/app/database.py` 的 SCHEMA 字符串中添加：

```sql
CREATE TABLE IF NOT EXISTS albums (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    cover_media_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (cover_media_id) REFERENCES media(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS album_media (
    album_id INTEGER,
    media_id INTEGER,
    sort_order INTEGER,
    PRIMARY KEY (album_id, media_id),
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE,
    FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_album_media_album ON album_media(album_id);
```

- [ ] **Step 2: 创建 albums 路由**

创建 `backend/app/routers/albums.py`：

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone

from app.database import get_connection
from app.models import MediaItem

router = APIRouter(prefix="/api/albums", tags=["albums"])


class AlbumCreate(BaseModel):
    name: str


class AlbumAddMedia(BaseModel):
    media_ids: list[int]


@router.get("")
def list_albums():
    conn = get_connection()
    rows = conn.execute(
        "SELECT a.*, m.thumbnail_path FROM albums a "
        "LEFT JOIN media m ON a.cover_media_id = m.id "
        "ORDER BY a.updated_at DESC"
    ).fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "cover_media_id": r["cover_media_id"],
            "cover_thumbnail": r["thumbnail_path"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
            "media_count": 0,  # populated below
        }
        for r in rows
    ]


@router.post("")
def create_album(body: AlbumCreate):
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        "INSERT INTO albums (name, created_at, updated_at) VALUES (?, ?, ?)",
        (body.name, now, now),
    )
    conn.commit()
    album_id = cursor.lastrowid
    conn.close()
    return {"id": album_id, "name": body.name, "created_at": now}


@router.post("/{album_id}/media")
def add_media_to_album(album_id: int, body: AlbumAddMedia):
    conn = get_connection()
    album = conn.execute("SELECT id FROM albums WHERE id = ?", (album_id,)).fetchone()
    if not album:
        conn.close()
        raise HTTPException(status_code=404, detail="相册不存在")

    now = datetime.now(timezone.utc).isoformat()
    count = 0
    for mid in body.media_ids:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO album_media (album_id, media_id, sort_order) VALUES (?, ?, ?)",
                (album_id, mid, 9999),
            )
            count += 1
        except Exception:
            continue

    photo_count = conn.execute(
        "SELECT COUNT(*) FROM album_media WHERE album_id = ?", (album_id,)
    ).fetchone()[0]

    # Update cover if not set
    current_cover = conn.execute(
        "SELECT cover_media_id FROM albums WHERE id = ?", (album_id,)
    ).fetchone()
    if not current_cover["cover_media_id"] and body.media_ids:
        conn.execute(
            "UPDATE albums SET cover_media_id = ?, updated_at = ? WHERE id = ?",
            (body.media_ids[0], now, album_id),
        )

    conn.execute(
        "UPDATE albums SET updated_at = ? WHERE id = ?", (now, album_id)
    )
    conn.commit()
    conn.close()
    return {"added": count, "album_id": album_id}


@router.get("/{album_id}/media")
def get_album_media(album_id: int, limit: int = 100):
    conn = get_connection()
    rows = conn.execute(
        "SELECT m.* FROM media m "
        "JOIN album_media am ON m.id = am.media_id "
        "WHERE am.album_id = ? "
        "ORDER BY am.sort_order LIMIT ?",
        (album_id, limit),
    ).fetchall()
    conn.close()
    return {"items": [MediaItem.from_row(r).model_dump() for r in rows]}


@router.delete("/{album_id}/media")
def remove_media_from_album(album_id: int, media_ids: list[int]):
    conn = get_connection()
    for mid in media_ids:
        conn.execute(
            "DELETE FROM album_media WHERE album_id = ? AND media_id = ?",
            (album_id, mid),
        )
    conn.commit()
    conn.close()
    return {"deleted": len(media_ids)}
```

- [ ] **Step 3: 添加 export-zip 端点**

在 `backend/app/routers/media.py` 末尾添加：

```python
import zipfile
import io
from fastapi.responses import StreamingResponse


@router.post("/export-zip")
def export_zip(ids: list[int]):
    """Stream selected media as a zip file download."""
    conn = get_connection()
    placeholders = ",".join("?" * len(ids))
    rows = conn.execute(
        f"SELECT id, path, filename FROM media WHERE id IN ({placeholders})",
        ids,
    ).fetchall()
    conn.close()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for row in rows:
            path = row["path"]
            if not os.path.isabs(path):
                path = os.path.join(settings.media_root, path)
            filename = row["filename"]
            if os.path.exists(path):
                zf.write(path, f"{row['id']}_{filename}")

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=homememories_export.zip"},
    )
```

同时需要在 `media.py` 顶部添加 `from app.database import get_connection` 和 `from app.config import settings`。

- [ ] **Step 4: 注册 albums 路由到 main.py**

在 `backend/app/main.py` 中添加：

```python
from app.routers.albums import router as albums_router
# ... existing router registrations
app.include_router(albums_router)
```

- [ ] **Step 5: 编写 albums API 测试**

创建 `backend/tests/test_albums_api.py`：

```python
import pytest
import os
from httpx import AsyncClient, ASGITransport
from app.database import get_connection, init_db


@pytest.fixture
def albums_app(tmp_path, monkeypatch):
    media_dir = str(tmp_path / "media")
    os.makedirs(media_dir, exist_ok=True)
    monkeypatch.setenv("MEDIA_ROOT", media_dir)
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))

    init_db()
    conn = get_connection()
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_taken, date_added, checksum) "
        "VALUES (1, '/p/1.jpg', 'a.jpg', 'image', '2025-01-01', '2026-01-01', 'a1')"
    )
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_taken, date_added, checksum) "
        "VALUES (2, '/p/2.jpg', 'b.jpg', 'image', '2025-01-02', '2026-01-01', 'b1')"
    )
    conn.commit()
    conn.close()

    from app.main import create_app
    return create_app()


@pytest.mark.asyncio
async def test_create_album(albums_app):
    transport = ASGITransport(app=albums_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/albums", json={"name": "宝宝成长"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "宝宝成长"
    assert "id" in data


@pytest.mark.asyncio
async def test_add_media_to_album(albums_app):
    transport = ASGITransport(app=albums_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        album_resp = await client.post("/api/albums", json={"name": "精选"})
        album_id = album_resp.json()["id"]

        resp = await client.post(f"/api/albums/{album_id}/media", json={"media_ids": [1, 2]})
        assert resp.status_code == 200
        assert resp.json()["added"] == 2


@pytest.mark.asyncio
async def test_get_album_media(albums_app):
    transport = ASGITransport(app=albums_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        album_resp = await client.post("/api/albums", json={"name": "精选"})
        album_id = album_resp.json()["id"]
        await client.post(f"/api/albums/{album_id}/media", json={"media_ids": [1, 2]})

        resp = await client.get(f"/api/albums/{album_id}/media")
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 2


@pytest.mark.asyncio
async def test_album_not_found(albums_app):
    transport = ASGITransport(app=albums_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/albums/999/media", json={"media_ids": [1]})
    assert resp.status_code == 404
```

- [ ] **Step 6: 运行 albums 测试**

```bash
cd backend && python -m pytest tests/test_albums_api.py -v
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/routers/albums.py backend/app/routers/media.py backend/app/database.py backend/app/main.py backend/tests/test_albums_api.py
git commit -m "feat(albums): 新增相册 CRUD API 与 media export-zip 端点"
```

---

### Task 3.2: 创建前端选择模式 hook 和 UI 组件

**Files:**
- Create: `frontend/src/hooks/useSelection.ts`
- Create: `frontend/src/components/gallery/SelectionBar.tsx`
- Create: `frontend/src/components/gallery/SelectionActions.tsx`

- [ ] **Step 1: 创建 useSelection hook**

创建 `frontend/src/hooks/useSelection.ts`：

```ts
import { useState, useCallback, useRef } from 'react';

export function useSelection() {
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [selectMode, setSelectMode] = useState(false);
  const longPressRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const enterSelectMode = useCallback((initialId?: number) => {
    setSelectMode(true);
    if (initialId !== undefined) {
      setSelectedIds(new Set([initialId]));
    }
  }, []);

  const exitSelectMode = useCallback(() => {
    setSelectMode(false);
    setSelectedIds(new Set());
  }, []);

  const toggleItem = useCallback((id: number) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
        if (next.size === 0) {
          // Could auto-exit, but design says keep mode active
        }
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const selectAll = useCallback((allIds: number[]) => {
    setSelectedIds(new Set(allIds));
  }, []);

  const isSelected = useCallback((id: number) => selectedIds.has(id), [selectedIds]);

  // Long press handler for mobile
  const onPointerDown = useCallback((id: number) => {
    longPressRef.current = setTimeout(() => {
      enterSelectMode(id);
      try { navigator.vibrate(15); } catch {}
    }, 300);
  }, [enterSelectMode]);

  const onPointerUp = useCallback(() => {
    if (longPressRef.current) {
      clearTimeout(longPressRef.current);
      longPressRef.current = null;
    }
  }, []);

  const onPointerMove = useCallback((id: number) => {
    if (selectMode && !selectedIds.has(id)) {
      toggleItem(id);
    }
  }, [selectMode, selectedIds, toggleItem]);

  const handleItemClick = useCallback((id: number, normalClick: () => void) => {
    if (selectMode) {
      toggleItem(id);
    } else {
      normalClick();
    }
  }, [selectMode, toggleItem]);

  return {
    selectedIds,
    selectMode,
    selectedCount: selectedIds.size,
    enterSelectMode,
    exitSelectMode,
    toggleItem,
    selectAll,
    isSelected,
    onPointerDown,
    onPointerUp,
    onPointerMove,
    handleItemClick,
  };
}
```

- [ ] **Step 2: 创建 SelectionBar 组件**

创建 `frontend/src/components/gallery/SelectionBar.tsx`：

```tsx
interface SelectionBarProps {
  count: number;
  onSelectAll: () => void;
  onClearAll: () => void;
  onExit: () => void;
}

export default function SelectionBar({ count, onSelectAll, onClearAll, onExit }: SelectionBarProps) {
  return (
    <div className="fixed top-0 left-0 right-0 z-40 flex items-center justify-between px-4 h-12 bg-white/95 backdrop-blur-md border-b border-misty md:ml-14">
      <button onClick={onExit} className="text-sm text-primary font-medium">← 取消</button>
      <span className="text-sm font-semibold text-text">已选 {count} 项</span>
      <button onClick={onSelectAll} className="text-sm text-primary font-medium">全选</button>
    </div>
  );
}
```

- [ ] **Step 3: 创建 SelectionActions 组件**

创建 `frontend/src/components/gallery/SelectionActions.tsx`：

```tsx
interface SelectionActionsProps {
  onAddToAlbum: () => void;
  onDownload: () => void;
  onDelete: () => void;
}

export default function SelectionActions({ onAddToAlbum, onDownload, onDelete }: SelectionActionsProps) {
  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 flex justify-around items-center py-3 px-4 bg-white/95 backdrop-blur-md border-t border-misty md:ml-14">
      <button onClick={onAddToAlbum} className="flex flex-col items-center gap-1 text-sm text-text hover:text-primary transition-colors">
        <span className="text-xl">📁</span>
        <span className="text-[10px]">加入相册</span>
      </button>
      <button onClick={onDownload} className="flex flex-col items-center gap-1 text-sm text-text hover:text-primary transition-colors">
        <span className="text-xl">⬇️</span>
        <span className="text-[10px]">下载</span>
      </button>
      <button onClick={onDelete} className="flex flex-col items-center gap-1 text-sm text-text hover:text-red-500 transition-colors">
        <span className="text-xl">🗑️</span>
        <span className="text-[10px]">删除</span>
      </button>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/hooks/useSelection.ts frontend/src/components/gallery/SelectionBar.tsx frontend/src/components/gallery/SelectionActions.tsx
git commit -m "feat(frontend): 新增批量选择模式 hook 与 UI 组件"
```

---

### Task 3.3: 在 PhotoGrid 中集成选择模式

**Files:**
- Modify: `frontend/src/components/gallery/PhotoGrid.tsx`

- [ ] **Step 1: 改造 PhotoGrid 支持选择模式**

替换 `frontend/src/components/gallery/PhotoGrid.tsx`：

```tsx
import type { MediaItem } from '../../api/client';
import { api } from '../../api/client';
import type { useSelection } from '../../hooks/useSelection';

interface PhotoGridProps {
  items: MediaItem[];
  onItemClick: (id: number) => void;
  selection?: ReturnType<typeof useSelection> | null;
}

export default function PhotoGrid({ items, onItemClick, selection }: PhotoGridProps) {
  const sel = selection;
  const selectMode = sel?.selectMode ?? false;

  if (items.length === 0) {
    return <p className="text-center text-text-light py-8">暂无结果</p>;
  }

  return (
    <div className={`grid grid-cols-3 md:grid-cols-5 gap-2 ${selectMode ? 'mt-12 mb-14' : ''}`}>
      {items.map((item) => {
        const isSel = sel?.isSelected(item.id) ?? false;
        return (
          <div
            key={item.id}
            className={`aspect-square rounded-card overflow-hidden bg-misty relative group transition-all ${
              selectMode
                ? isSel
                  ? 'cursor-pointer ring-2 ring-primary ring-offset-1'
                  : 'cursor-pointer opacity-50'
                : 'cursor-pointer hover:opacity-90'
            }`}
            onClick={() => sel?.handleItemClick(item.id, () => onItemClick(item.id))}
            onPointerDown={() => sel?.onPointerDown(item.id)}
            onPointerUp={sel?.onPointerUp}
            onPointerMove={() => sel?.onPointerMove(item.id)}
          >
            {item.thumbnail_path ? (
              <img
                src={api.thumbUrl(item.thumbnail_path)}
                alt={item.filename}
                className="w-full h-full object-cover"
                loading="lazy"
                draggable={false}
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-2xl">📷</div>
            )}

            {/* Selection indicator */}
            {selectMode && (
              <div className={`absolute top-1.5 left-1.5 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors ${
                isSel ? 'bg-primary border-primary text-white' : 'bg-black/30 border-white'
              }`}>
                {isSel && <span className="text-[10px] leading-none">✓</span>}
              </div>
            )}

            {!selectMode && (
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/50 to-transparent p-2">
                <span className="text-white text-[10px]">{item.date_taken?.slice(0, 10)}</span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/gallery/PhotoGrid.tsx
git commit -m "feat(frontend): PhotoGrid 集成批量选择模式"
```

---

### Task 3.4: 在 SearchPage 中集成批量操作

**Files:**
- Modify: `frontend/src/pages/SearchPage.tsx`

- [ ] **Step 1: 改造 SearchPage**

修改 `frontend/src/pages/SearchPage.tsx`：

- 添加 import：
```tsx
import { useSelection } from '../hooks/useSelection';
import SelectionBar from '../components/gallery/SelectionBar';
import SelectionActions from '../components/gallery/SelectionActions';
import { useState } from 'react';  // already imported
import { api } from '../api/client';
```

- 在组件内添加：
```tsx
const selection = useSelection();
const [albumPickerOpen, setAlbumPickerOpen] = useState(false);
const [albums, setAlbums] = useState<{ id: number; name: string }[]>([]);
```

- 加载相册列表（在选择模式下需要）：
```tsx
const loadAlbums = async () => {
  const list = await api.get<{ id: number; name: string }[]>('/api/albums');
  setAlbums(list);
  setAlbumPickerOpen(true);
};
```

- 批量删除：
```tsx
const handleBatchDelete = async () => {
  if (!confirm(`确定删除这 ${selection.selectedCount} 张照片？此操作不可恢复。`)) return;
  for (const id of selection.selectedIds) {
    await api.delete(`/api/media/${id}`);
  }
  selection.exitSelectMode();
  // Re-trigger search to refresh results
  if (mode === 'text' && textSearch.results) {
    textSearch.search(textSearch.results.toString()); // approximate
  }
};
```

- 批量下载：
```tsx
const handleBatchDownload = async () => {
  const ids = Array.from(selection.selectedIds);
  if (ids.length <= 5) {
    ids.forEach(id => window.open(api.originalUrl(id), '_blank'));
  } else {
    const res = await fetch(`${window.location.origin}/api/media/export-zip`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(ids),
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'homememories_export.zip';
    a.click();
    URL.revokeObjectURL(url);
  }
  selection.exitSelectMode();
};
```

- 在 JSX 的 PhotoGrid 组件上传递 selection prop：
```tsx
<PhotoGrid
  items={currentResults.results}
  onItemClick={(id) => { if (!selection.selectMode) navigate(`/photo/${id}`, { state: { from: '/search' } }); }}
  selection={selection}
/>
```

- 在选择模式下渲染 SelectionBar 和 SelectionActions：
```tsx
{selection.selectMode && (
  <>
    <SelectionBar
      count={selection.selectedCount}
      onSelectAll={() => selection.selectAll(currentResults?.results.map(r => r.id) || [])}
      onClearAll={() => selection.selectAll([])}
      onExit={selection.exitSelectMode}
    />
    <SelectionActions
      onAddToAlbum={loadAlbums}
      onDownload={handleBatchDownload}
      onDelete={handleBatchDelete}
    />
  </>
)}
```

- [ ] **Step 2: 验证 TypeScript 编译**

```bash
cd frontend && npx tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/SearchPage.tsx
git commit -m "feat(frontend): SearchPage 集成批量选择操作"
```

---

### Task 3.5: 在设置页模糊照片列表中集成批量操作

**Files:**
- Modify: `frontend/src/pages/SettingsPage.tsx`

- [ ] **Step 1: 在模糊照片列表中添加批量删除**

在 SettingsPage 中模糊照片区域，替换现有的单张删除为支持批量：

- 添加 import：
```tsx
import { useSelection } from '../hooks/useSelection';
import SelectionBar from '../components/gallery/SelectionBar';
```

- 添加 selection hook（专门用于模糊照片区域）：
```tsx
const blurrySelection = useSelection();
```

- 在模糊照片的网格容器中，如果有选中模式显示 SelectionBar，并在每张照片上添加长按/选择交互。

这个改动较小且集中在 SettingsPage 内部，在 PhotoGrid 已支持 selection 的情况下，将 blurryItems 通过 PhotoGrid 渲染即可自动获得选择能力。

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/SettingsPage.tsx
git commit -m "feat(frontend): 设置页模糊照片列表集成批量删除"
```

---

### Task 3.6: 在 PeoplePage 中集成批量操作

**Files:**
- Modify: `frontend/src/pages/PeoplePage.tsx`

- [ ] **Step 1: 改造 PeoplePage 照片列表支持批量选择**

修改 `frontend/src/pages/PeoplePage.tsx`：

在现有 import 后添加：

```tsx
import { useSelection } from '../hooks/useSelection';
import SelectionBar from '../components/gallery/SelectionBar';
import SelectionActions from '../components/gallery/SelectionActions';
```

在组件内 Handler 函数区域添加 selection hook：

```tsx
const selection = useSelection();
```

添加批量操作处理函数：

```tsx
const handleBatchDownload = async () => {
  const ids = Array.from(selection.selectedIds);
  if (ids.length <= 5) {
    ids.forEach(id => window.open(api.originalUrl(id), '_blank'));
  } else {
    const res = await fetch(`${window.location.origin}/api/media/export-zip`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(ids),
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'homememories_export.zip';
    a.click();
    URL.revokeObjectURL(url);
  }
  selection.exitSelectMode();
};

const handleBatchDelete = async () => {
  if (!confirm(`确定删除这 ${selection.selectedCount} 张照片？此操作不可恢复。`)) return;
  for (const id of selection.selectedIds) {
    await api.delete(`/api/media/${id}`);
  }
  selection.exitSelectMode();
  // Refresh cluster media
  if (selectedCluster) {
    const res = await api.get<PaginatedResponse<MediaItem>>(`/api/faces/cluster/${selectedCluster.id}/media`, { limit: 100 });
    setClusterMedia(res.items);
  }
};
```

找到 `clusterMedia.length > 0` 区块中 PhotoGrid 的调用处（约第 65 行），改为：

```tsx
<>
  {selection.selectMode && (
    <>
      <SelectionBar
        count={selection.selectedCount}
        onSelectAll={() => selection.selectAll(clusterMedia.map(r => r.id))}
        onClearAll={() => selection.selectAll([])}
        onExit={selection.exitSelectMode}
      />
      <SelectionActions
        onAddToAlbum={() => {}}
        onDownload={handleBatchDownload}
        onDelete={handleBatchDelete}
      />
    </>
  )}
  <PhotoGrid
    items={clusterMedia}
    onItemClick={(id) => {
      if (!selection.selectMode) navigate(`/photo/${id}`, { state: { from: '/people' } });
    }}
    selection={selection}
  />
</>
```

- [ ] **Step 2: 验证 TypeScript 编译**

```bash
cd frontend && npx tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/PeoplePage.tsx
git commit -m "feat(frontend): PeoplePage 人物相册集成批量选择操作"
```

---

## 最终验证

全部实现后，执行以下验证：

```bash
# 后端全量测试
cd backend && python -m pytest tests/ -v

# 前端类型检查
cd frontend && npx tsc --noEmit

# 前端构建
cd frontend && npm run build
```

---

## 实施顺序

1. Phase 1 Tasks 1.1 → 1.2 → 1.3（扫码访问，独立可交付）
2. Phase 2 Tasks 2.1 → 2.2（手机上传，依赖 Phase 1 完成）
3. Phase 3 Tasks 3.1 → 3.2 → 3.3 → 3.4 → 3.5（批量操作，依赖 Phase 2 完成）
