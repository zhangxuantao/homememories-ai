# backend/tests/test_face_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI


@pytest.fixture
def face_app():
    """Creates a minimal FastAPI app that includes only the faces router."""
    from app.routers.faces import router

    app = FastAPI()
    app.include_router(router)
    return app


@pytest.mark.asyncio
async def test_get_clusters_returns_empty(face_app):
    """GET /api/faces/clusters should return an empty list (Phase 3 stub)."""
    transport = ASGITransport(app=face_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/faces/clusters")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_cluster_media_returns_empty(face_app):
    """GET /api/faces/cluster/1/media should return empty items stub."""
    transport = ASGITransport(app=face_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/faces/cluster/1/media")
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"items": [], "next_cursor": None}


@pytest.mark.asyncio
async def test_patch_cluster_returns_501(face_app):
    """PATCH /api/faces/cluster/1 should return 501 Not Implemented."""
    transport = ASGITransport(app=face_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.patch(
            "/api/faces/cluster/1",
            params={"label": "Family"},
        )
    assert resp.status_code == 501
    assert "Not implemented" in resp.json()["detail"]
