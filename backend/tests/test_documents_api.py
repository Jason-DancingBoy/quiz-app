import pytest
import os
from urllib.parse import unquote
from httpx import ASGITransport, AsyncClient, BasicAuth
from sqlalchemy import select
from backend.main import app
from backend.database import init_db, async_session
from backend.models import Document


@pytest.fixture
async def client():
    auth = BasicAuth(os.environ.get("BASIC_AUTH_USER", "admin"), os.environ.get("BASIC_AUTH_PASS", "quiz2026"))
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", auth=auth
    ) as ac:
        yield ac


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()
    yield


@pytest.mark.asyncio
async def test_create_document_paste(client):
    resp = await client.post("/api/documents", json={"title": "test", "content": "Hello world content here."})
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "test"
    assert data["source_type"] == "paste"


@pytest.mark.asyncio
async def test_list_documents(client):
    await client.post("/api/documents", json={"title": "doc1", "content": "content1"})
    resp = await client.get("/api/documents")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_delete_document(client):
    resp = await client.post("/api/documents", json={"title": "to_delete", "content": "bye"})
    doc_id = resp.json()["id"]
    resp = await client.delete(f"/api/documents/{doc_id}")
    assert resp.status_code == 200
    resp = await client.get("/api/documents")
    assert all(d["id"] != doc_id for d in resp.json())


@pytest.mark.asyncio
async def test_download_uploaded_file(client):
    resp = await client.post(
        "/api/documents/upload",
        files={"file": ("notes.txt", b"hello from upload", "text/plain")},
    )
    assert resp.status_code == 200
    doc_id = resp.json()["id"]

    resp = await client.get(f"/api/documents/{doc_id}/download")
    assert resp.status_code == 200
    assert resp.content == b"hello from upload"
    assert "notes.txt" in resp.headers["content-disposition"]

    # cleanup: 删除接口会同时移除磁盘文件
    resp = await client.delete(f"/api/documents/{doc_id}")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_download_uploaded_file_chinese_title(client):
    """Upload with a Chinese filename round-trips through FileResponse filename*."""
    title = "中文笔记.md"
    resp = await client.post(
        "/api/documents/upload",
        files={"file": (title, "# 中文".encode("utf-8"), "text/markdown")},
    )
    assert resp.status_code == 200
    doc_id = resp.json()["id"]

    resp = await client.get(f"/api/documents/{doc_id}/download")
    assert resp.status_code == 200
    assert resp.content == "# 中文".encode("utf-8")
    assert title in unquote(resp.headers["content-disposition"])

    # cleanup: 删除接口会同时移除磁盘文件
    resp = await client.delete(f"/api/documents/{doc_id}")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_download_uploaded_file_missing_on_disk(client):
    """Upload whose disk file was removed still exists in DB -> download returns 404."""
    resp = await client.post(
        "/api/documents/upload",
        files={"file": ("gone.txt", b"will vanish", "text/plain")},
    )
    assert resp.status_code == 200
    doc_id = resp.json()["id"]

    # Simulate the disk file going missing (e.g. manual deletion/cleanup job).
    async with async_session() as db:
        doc = await db.execute(select(Document).where(Document.id == doc_id))
        doc = doc.scalar_one()
        assert doc.file_path and os.path.exists(doc.file_path)
        os.remove(doc.file_path)

    resp = await client.get(f"/api/documents/{doc_id}/download")
    assert resp.status_code == 404

    # cleanup: 删除接口容忍磁盘文件已缺失，同时移除 DB 行
    resp = await client.delete(f"/api/documents/{doc_id}")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_download_paste_document(client):
    resp = await client.post(
        "/api/documents",
        json={"title": "我的笔记", "content": "hello paste content"},
    )
    assert resp.status_code == 200
    doc_id = resp.json()["id"]

    resp = await client.get(f"/api/documents/{doc_id}/download")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    assert resp.text == "hello paste content"
    assert "笔记.txt" in unquote(resp.headers["content-disposition"])


@pytest.mark.asyncio
async def test_download_nonexistent_document(client):
    resp = await client.get("/api/documents/999999/download")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_download_paste_title_crlf_cleanup(client):
    """A paste title with control chars must not inject raw CRLF into Content-Disposition."""
    evil = "evil\r\nX-Evil: injected"
    resp = await client.post("/api/documents", json={"title": evil, "content": "content"})
    assert resp.status_code == 200
    doc_id = resp.json()["id"]

    resp = await client.get(f"/api/documents/{doc_id}/download")
    assert resp.status_code == 200
    header = resp.headers["content-disposition"]
    assert "\r" not in header
    assert "\n" not in header

    # cleanup: 删除接口会同时移除磁盘文件
    resp = await client.delete(f"/api/documents/{doc_id}")
    assert resp.status_code == 200
