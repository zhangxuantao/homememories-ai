# backend/tests/test_shares.py
import pytest
import os
import json
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.database import get_connection, init_db


@pytest.fixture
def shares_app(tmp_path, monkeypatch):
    media_dir = str(tmp_path / "media")
    os.makedirs(media_dir, exist_ok=True)
    monkeypatch.setenv("MEDIA_ROOT", media_dir)
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))

    init_db()

    conn = get_connection()
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_added) VALUES (?, ?, ?, ?, ?)",
        (1, "/test/a.jpg", "a.jpg", "image", "2026-01-01T00:00:00"),
    )
    conn.execute(
        "INSERT INTO media (id, path, filename, media_type, date_added) VALUES (?, ?, ?, ?, ?)",
        (2, "/test/b.jpg", "b.jpg", "image", "2026-01-02T00:00:00"),
    )
    conn.commit()
    conn.close()

    from app.main import create_app
    return create_app()


def test_create_share(shares_app):
    client = TestClient(shares_app)
    resp = client.post("/api/shares", json={"media_ids": [1, 2], "title": "测试分享"})
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert len(data["token"]) == 16
    assert "/share/" in data["url"]


def test_create_share_empty(shares_app):
    client = TestClient(shares_app)
    resp = client.post("/api/shares", json={"media_ids": []})
    assert resp.status_code == 400


def test_list_shares(shares_app):
    client = TestClient(shares_app)
    client.post("/api/shares", json={"media_ids": [1]})
    resp = client.get("/api/shares")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_view_share(shares_app):
    client = TestClient(shares_app)
    create_resp = client.post("/api/shares", json={"media_ids": [1, 2]})
    token = create_resp.json()["token"]

    resp = client.get(f"/api/share/{token}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["media"]) == 2
    assert data["media"][0]["filename"] == "a.jpg"


def test_view_share_invalid_token(shares_app):
    client = TestClient(shares_app)
    resp = client.get("/api/share/nonexistent123")
    assert resp.status_code == 404


def test_view_share_expired(shares_app):
    client = TestClient(shares_app)
    conn = get_connection()
    expired = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    conn.execute(
        "INSERT INTO shares (token, media_ids, expires_at, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
        ("expiredtoken", json.dumps([1]), expired, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()

    resp = client.get("/api/share/expiredtoken")
    assert resp.status_code == 410


def test_revoke_share(shares_app):
    client = TestClient(shares_app)
    client.post("/api/shares", json={"media_ids": [1]})
    share_id = client.get("/api/shares").json()[0]["id"]

    resp = client.delete(f"/api/shares/{share_id}")
    assert resp.status_code == 200

    list_resp = client.get("/api/shares")
    assert len(list_resp.json()) == 0


def test_revoke_nonexistent(shares_app):
    client = TestClient(shares_app)
    resp = client.delete("/api/shares/999")
    assert resp.status_code == 404
