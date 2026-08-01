import os
import pytest
from httpx import ASGITransport, AsyncClient, BasicAuth
from backend.main import app
from backend.database import init_db, async_session
from backend.models import Document, Quiz, Question, Attempt


AUTH = BasicAuth(os.environ.get("BASIC_AUTH_USER", "admin"), os.environ.get("BASIC_AUTH_PASS", "quiz2026"))


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", auth=AUTH) as ac:
        yield ac


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()
    yield


async def _create_doc(client, title="test doc", content="Some content for testing."):
    resp = await client.post("/api/documents", json={"title": title, "content": content})
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_generate_triggers_async(client):
    doc_id = await _create_doc(client)
    resp = await client.post(
        f"/api/documents/{doc_id}/generate",
        json={"difficulty": "medium", "question_count": 5},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "generating"
    assert "id" in data


@pytest.mark.asyncio
async def test_generate_duplicate_returns_409(client):
    doc_id = await _create_doc(client)
    await client.post(f"/api/documents/{doc_id}/generate", json={"difficulty": "easy", "question_count": 5})
    resp = await client.post(f"/api/documents/{doc_id}/generate", json={"difficulty": "easy", "question_count": 5})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_get_quiz_polling(client):
    doc_id = await _create_doc(client)
    resp = await client.post(f"/api/documents/{doc_id}/generate", json={"difficulty": "easy", "question_count": 5})
    quiz_id = resp.json()["id"]

    resp = await client.get(f"/api/quizzes/{quiz_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("generating", "ready")
    if data["status"] == "generating":
        assert "progress" in data


@pytest.mark.asyncio
async def test_submit_twice_returns_409(client):
    doc_id = await _create_doc(client)

    # Directly create a ready quiz with questions
    from backend.database import async_session
    from sqlalchemy import select
    async with async_session() as db:
        quiz = Quiz(document_id=doc_id, status="ready", difficulty="easy", total=2)
        db.add(quiz)
        await db.flush()
        q1 = Question(quiz_id=quiz.id, content="Q1", options=["A","B","C","D"], correct_index=0, explanation="E1", order_num=1)
        q2 = Question(quiz_id=quiz.id, content="Q2", options=["A","B","C","D"], correct_index=1, explanation="E2", order_num=2)
        db.add_all([q1, q2])
        await db.flush()
        q1_id, q2_id = q1.id, q2.id
        quiz_id = quiz.id
        await db.commit()

    resp = await client.post(f"/api/quizzes/{quiz_id}/submit", json={
        "answers": [
            {"question_id": q1_id, "selected_index": 0},
            {"question_id": q2_id, "selected_index": 0},
        ]
    })
    assert resp.status_code == 200

    resp = await client.post(f"/api/quizzes/{quiz_id}/submit", json={
        "answers": [{"question_id": q1_id, "selected_index": 0}]
    })
    assert resp.status_code == 409
