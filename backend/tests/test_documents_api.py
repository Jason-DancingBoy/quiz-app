import pytest
import os
from httpx import ASGITransport, AsyncClient, BasicAuth
from backend.main import app
from backend.database import init_db


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
