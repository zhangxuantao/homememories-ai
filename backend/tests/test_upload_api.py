# backend/tests/test_upload_api.py
import pytest
import os
from httpx import AsyncClient, ASGITransport
from app.database import init_db


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
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    for i, color in enumerate(colors):
        p = str(tmp_path / f"img{i}.jpg")
        Image.new("RGB", (50, 50), color=color).save(p, "JPEG")
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
