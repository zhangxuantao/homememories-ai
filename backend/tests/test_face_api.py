# backend/tests/test_face_api.py
import pytest
import tempfile
import os
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI


@pytest.fixture
def face_app():
    """Creates a FastAPI app with faces router, using a temp database."""
    from app.routers.faces import router

    app = FastAPI()
    app.include_router(router)
    return app


@pytest.mark.asyncio
async def test_get_clusters_returns_list(face_app):
    """GET /api/faces/clusters should return a list (may be empty)."""
    transport = ASGITransport(app=face_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/faces/clusters")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_get_cluster_media_returns_paginated(face_app):
    """GET /api/faces/cluster/1/media should return paginated response."""
    transport = ASGITransport(app=face_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/faces/cluster/1/media")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "next_cursor" in data


@pytest.mark.asyncio
async def test_patch_nonexistent_cluster_returns_404(face_app):
    """PATCH /api/faces/cluster/999999 should return 404."""
    transport = ASGITransport(app=face_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.patch(
            "/api/faces/cluster/999999",
            params={"label": "Family"},
        )
    assert resp.status_code == 404
