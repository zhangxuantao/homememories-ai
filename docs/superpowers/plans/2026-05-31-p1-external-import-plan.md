# 外部导入 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 Google Takeout zip 和 iCloud 目录的外部导入功能，复制照片到本地并自动触发扫描。

**Architecture:** 后端新建 `import_photos.py` 路由，两个端点分别处理 Takeout zip 上传解压和 iCloud 目录遍历复制，完成复制后用 `requests` 调用现有 scan API。前端在 SettingsPage 新增"外部导入"卡片。

**Tech Stack:** Python/FastAPI/zipfile/shutil 后端 + React/TypeScript 前端

---

### Task 1: 后端 — import_photos 路由

**Files:**
- Create: `backend/app/routers/import_photos.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_import_photos.py`

**Depends on:** Nothing

- [ ] **Step 1: 创建 import_photos.py**

```python
# backend/app/routers/import_photos.py
import os
import shutil
import zipfile
import tempfile
import uuid
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/api/import", tags=["import"])

ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif",
    ".heic", ".heif",
    ".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v",
}

SKIP_FILES = {".ds_store", "thumbs.db", "desktop.ini", "archive_browser.html"}


def _is_media_file(filename: str) -> bool:
    name = os.path.basename(filename).lower()
    if name in SKIP_FILES:
        return False
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def _copy_media_files(src_dir: str, dest_dir: str) -> int:
    """Recursively copy media files from src_dir to dest_dir. Returns count."""
    os.makedirs(dest_dir, exist_ok=True)
    count = 0
    for root, dirs, files in os.walk(src_dir):
        for f in files:
            if _is_media_file(f):
                src_path = os.path.join(root, f)
                # Use UUID to avoid name collisions
                ext = os.path.splitext(f)[1].lower()
                dest_path = os.path.join(dest_dir, f"{uuid.uuid4().hex}{ext}")
                shutil.copy2(src_path, dest_path)
                count += 1
    return count


def _trigger_scan(path: str) -> dict:
    """Call the scan API on the imported directory."""
    import requests
    try:
        resp = requests.post(
            f"http://localhost:{settings.server_port}/api/admin/scan",
            json={"path": path},
            timeout=5,
        )
        return resp.json()
    except Exception:
        return {"job_id": "scan_triggered", "status": "pending"}


class ICloudImportRequest(BaseModel):
    source_dir: str


@router.post("/takeout")
async def import_takeout(file: UploadFile = File(...)):
    """Upload and extract a Google Takeout zip file."""
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="请上传 .zip 文件")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_dir = os.path.join(settings.media_root, "imports", f"takeout_{ts}")

    # Save uploaded zip to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Extract to temp directory
        extract_dir = tempfile.mkdtemp()
        with zipfile.ZipFile(tmp_path, "r") as zf:
            zf.extractall(extract_dir)

        # Copy media files from extracted content to destination
        count = _copy_media_files(extract_dir, dest_dir)

        if count == 0:
            raise HTTPException(status_code=400, detail="zip 文件中未找到照片或视频")

        # Cleanup temp files
        shutil.rmtree(extract_dir, ignore_errors=True)

        # Trigger scan
        scan_result = _trigger_scan(dest_dir)

        return {"imported": count, "destination": dest_dir, "scan": scan_result}

    finally:
        # Cleanup temp zip
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/icloud")
def import_icloud(body: ICloudImportRequest):
    """Import photos from an iCloud export directory."""
    source_dir = os.path.expanduser(body.source_dir)
    if not os.path.isdir(source_dir):
        raise HTTPException(status_code=400, detail="目录不存在或无法访问")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_dir = os.path.join(settings.media_root, "imports", f"icloud_{ts}")

    count = _copy_media_files(source_dir, dest_dir)

    if count == 0:
        raise HTTPException(status_code=400, detail="目录中未找到照片或视频")

    scan_result = _trigger_scan(dest_dir)

    return {"imported": count, "destination": dest_dir, "scan": scan_result}
```

- [ ] **Step 2: 在 main.py 注册路由**

在 `backend/app/main.py` 的路由导入区域添加：

```python
from app.routers import import_photos

app.include_router(import_photos.router)
```

- [ ] **Step 3: 编写测试**

```python
# backend/tests/test_import_photos.py
import os
import io
import zipfile
import tempfile
from fastapi.testclient import TestClient
from PIL import Image
from app.main import app

client = TestClient(app)


def _create_test_zip(contents: dict) -> bytes:
    """Create a zip file in memory. contents: {filename: bytes}"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in contents.items():
            zf.writestr(name, data)
    buf.seek(0)
    return buf.read()


def test_import_takeout_empty_zip(monkeypatch):
    """Takeout with no media files should return 400."""
    monkeypatch.setenv("MEDIA_ROOT", tempfile.mkdtemp())
    monkeypatch.setenv("DATA_ROOT", tempfile.mkdtemp())
    # Reload config
    from app import config
    monkeypatch.setattr(config.settings, "media_root", tempfile.mkdtemp())
    monkeypatch.setattr(config.settings, "data_root", tempfile.mkdtemp())
    monkeypatch.setattr(config.settings, "server_port", 8501)

    zip_data = _create_test_zip({"readme.txt": b"hello"})
    resp = client.post(
        "/api/import/takeout",
        files={"file": ("test.zip", io.BytesIO(zip_data), "application/zip")},
    )
    assert resp.status_code == 400
    assert "未找到照片" in resp.json()["detail"]


def test_import_takeout_with_images(monkeypatch):
    """Takeout with actual images should succeed."""
    media_root = tempfile.mkdtemp()
    monkeypatch.setenv("MEDIA_ROOT", media_root)
    monkeypatch.setenv("DATA_ROOT", tempfile.mkdtemp())
    monkeypatch.setenv("SERVER_PORT", "0")  # Disable scan trigger for test
    from app import config
    monkeypatch.setattr(config.settings, "media_root", media_root)
    monkeypatch.setattr(config.settings, "data_root", tempfile.mkdtemp())
    monkeypatch.setattr(config.settings, "server_port", 0)

    # Create test images
    img1 = io.BytesIO()
    Image.new("RGB", (100, 100), "red").save(img1, "JPEG")
    img1.seek(0)

    img2 = io.BytesIO()
    Image.new("RGB", (200, 200), "blue").save(img2, "JPEG")
    img2.seek(0)

    zip_data = _create_test_zip({
        "photos/img1.jpg": img1.read(),
        "photos/img2.jpg": img2.read(),
        "photos/metadata.json": b'{"title":"test"}',
    })

    resp = client.post(
        "/api/import/takeout",
        files={"file": ("takeout.zip", io.BytesIO(zip_data), "application/zip")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 2
    assert "takeout_" in data["destination"]


def test_import_takeout_not_zip(monkeypatch):
    """Non-zip file should return 400."""
    monkeypatch.setenv("MEDIA_ROOT", tempfile.mkdtemp())
    monkeypatch.setenv("DATA_ROOT", tempfile.mkdtemp())
    from app import config
    monkeypatch.setattr(config.settings, "media_root", tempfile.mkdtemp())
    monkeypatch.setattr(config.settings, "data_root", tempfile.mkdtemp())

    resp = client.post(
        "/api/import/takeout",
        files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert resp.status_code == 400


def test_import_icloud_dir_not_found(monkeypatch):
    """Non-existent directory should return 400."""
    monkeypatch.setenv("MEDIA_ROOT", tempfile.mkdtemp())
    monkeypatch.setenv("DATA_ROOT", tempfile.mkdtemp())
    monkeypatch.setenv("SERVER_PORT", "0")
    from app import config
    monkeypatch.setattr(config.settings, "media_root", tempfile.mkdtemp())
    monkeypatch.setattr(config.settings, "data_root", tempfile.mkdtemp())
    monkeypatch.setattr(config.settings, "server_port", 0)

    resp = client.post("/api/import/icloud", json={"source_dir": "/nonexistent/path/xyz"})
    assert resp.status_code == 400


def test_import_icloud_with_images(monkeypatch):
    """Valid directory with images should succeed."""
    media_root = tempfile.mkdtemp()
    source_dir = tempfile.mkdtemp()
    monkeypatch.setenv("MEDIA_ROOT", media_root)
    monkeypatch.setenv("DATA_ROOT", tempfile.mkdtemp())
    monkeypatch.setenv("SERVER_PORT", "0")
    from app import config
    monkeypatch.setattr(config.settings, "media_root", media_root)
    monkeypatch.setattr(config.settings, "data_root", tempfile.mkdtemp())
    monkeypatch.setattr(config.settings, "server_port", 0)

    # Create test images in source directory
    Image.new("RGB", (100, 100), "red").save(os.path.join(source_dir, "photo1.jpg"), "JPEG")
    Image.new("RGB", (200, 200), "blue").save(os.path.join(source_dir, "photo2.png"), "PNG")
    # Create a non-media file that should be skipped
    with open(os.path.join(source_dir, ".DS_Store"), "w") as f:
        f.write("skip me")

    resp = client.post("/api/import/icloud", json={"source_dir": source_dir})
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 2
    assert "icloud_" in data["destination"]
```

- [ ] **Step 4: 运行测试**

```bash
cd backend && python -m pytest tests/test_import_photos.py -v
```

预期: 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/import_photos.py backend/app/main.py backend/tests/test_import_photos.py
git commit -m "feat(import): 新增外部导入端点 — Takeout zip + iCloud 目录"
```

---

### Task 2: 前端 — SettingsPage 新增外部导入卡片

**Files:**
- Modify: `frontend/src/pages/SettingsPage.tsx`

**Depends on:** Task 1

- [ ] **Step 1: 在 SettingsPage 添加外部导入 Section**

在 `frontend/src/pages/SettingsPage.tsx` 中，找到最后一个 `</Section>`（清理工具 Section 之后），在其后添加：

```tsx
      <Section title="外部导入">
        {/* Google Takeout */}
        <div className="mb-4">
          <h4 className="text-sm font-medium text-text mb-1">Google Takeout</h4>
          <p className="text-xs text-text-light mb-2">
            从 Google Takeout 导出的 .zip 文件导入照片
          </p>
          <input
            type="file"
            accept=".zip"
            onChange={async (e) => {
              const file = e.target.files?.[0];
              if (!file) return;
              const formData = new FormData();
              formData.append('file', file);
              try {
                setJobStatus({ status: 'running', progress: 0, job_id: '', error: null });
                const res = await fetch(`${window.location.origin}/api/import/takeout`, {
                  method: 'POST',
                  body: formData,
                });
                const data = await res.json();
                if (res.ok) {
                  alert(`导入成功！已导入 ${data.imported} 张照片到 ${data.destination}`);
                  setJobStatus({ status: 'completed', progress: 100, job_id: '', error: null });
                } else {
                  throw new Error(data.detail);
                }
              } catch (err) {
                alert('导入失败: ' + (err as Error).message);
                setJobStatus({ status: 'failed', progress: 0, job_id: '', error: (err as Error).message });
              }
              e.target.value = '';
            }}
            className="block w-full text-sm text-text-light file:mr-3 file:py-1.5 file:px-4 file:rounded-btn file:border-0 file:text-sm file:font-medium file:bg-primary file:text-white hover:file:opacity-90 file:cursor-pointer"
          />
          {jobStatus.status === 'running' && (
            <div className="glass-card rounded-card p-3 text-sm mt-2">
              导入中...
              {jobStatus.progress > 0 && <span> {Math.round(jobStatus.progress)}%</span>}
            </div>
          )}
        </div>

        {/* iCloud */}
        <div>
          <h4 className="text-sm font-medium text-text mb-1">iCloud 照片</h4>
          <p className="text-xs text-text-light mb-2">
            从 iCloud 导出的照片目录一键迁移
          </p>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="输入 iCloud 照片目录路径，如 D:\iCloud Photos"
              className="flex-1 px-3 py-2 border border-misty rounded-btn text-sm outline-none focus:border-primary"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  const path = (e.target as HTMLInputElement).value.trim();
                  if (!path) return;
                  setJobStatus({ status: 'running', progress: 0, job_id: '', error: null });
                  fetch(`${window.location.origin}/api/import/icloud`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ source_dir: path }),
                  })
                    .then(res => res.json().then(data => ({ ok: res.ok, data })))
                    .then(({ ok, data }) => {
                      if (ok) {
                        alert(`导入成功！已导入 ${data.imported} 张照片`);
                        setJobStatus({ status: 'completed', progress: 100, job_id: '', error: null });
                      } else {
                        throw new Error(data.detail);
                      }
                    })
                    .catch(err => {
                      alert('导入失败: ' + (err as Error).message);
                      setJobStatus({ status: 'failed', progress: 0, job_id: '', error: (err as Error).message });
                    });
                  (e.target as HTMLInputElement).value = '';
                }
              }}
            />
          </div>
        </div>
      </Section>
```

确认 `jobStatus` state 和 `setJobStatus` 已在页面中定义（它们用于扫描进度，应该已存在）。

- [ ] **Step 2: 验证 TypeScript 编译**

```bash
cd frontend && npx tsc --noEmit
```

预期: 无错误

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/SettingsPage.tsx
git commit -m "feat(import): SettingsPage 新增外部导入卡片"
```

---

### Task 3: 端到端验证

**Depends on:** Tasks 1-2

- [ ] **Step 1: 运行后端测试**

```bash
cd backend && python -m pytest tests/test_import_photos.py -v
```

预期: 5 tests PASS

- [ ] **Step 2: 验证前端构建**

```bash
cd frontend && npm run build
```

预期: 构建成功

- [ ] **Step 3: Commit（如有修正）**

```bash
git add -A && git commit -m "chore: E2E 验证通过 — 导入端点 + 前端编译"
```
