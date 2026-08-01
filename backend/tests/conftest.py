"""pytest configuration for quiz-app tests.

Sets required environment variables before any backend imports so that
config.py resolves the correct paths when running outside Docker.
"""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Environment setup -- must happen before ANY backend import so config.py
# picks up non-Docker paths.
# conftest lives at backend/tests/conftest.py, so parents[2] is project root.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]

os.environ.setdefault("BASIC_AUTH_USER", "test")
os.environ.setdefault("BASIC_AUTH_PASS", "test")
os.environ.setdefault(
    "CHROMA_PERSIST_DIR",
    str(PROJECT_ROOT / "data" / "chroma"),
)
os.environ.setdefault(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{PROJECT_ROOT / 'data' / 'quiz.db'}",
)
os.environ.setdefault(
    "EMBEDDING_MODEL_PATH",
    str(
        PROJECT_ROOT
        / "models"
        / "hub"
        / "models--BAAI--bge-small-zh-v1.5"
        / "snapshots"
        / "7999e1d3359715c523056ef9478215996d62a620"
    ),
)

import pytest
from backend.routers.quizzes import cancel_background_tasks


@pytest.fixture(autouse=True)
async def cleanup_background_tasks():
    yield
    await cancel_background_tasks()
