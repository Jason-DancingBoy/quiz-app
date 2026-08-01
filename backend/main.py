import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from backend.auth import basic_auth_middleware
from backend.config import STATIC_DIR
from backend.database import init_db, async_session
from sqlalchemy import text
from backend.logger import get_logger
from backend.routers import documents, quizzes
from backend.services.rag_service import warmup_embedding_model

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized successfully")
    logger.info("Warming up embedding model...")
    await warmup_embedding_model()
    logger.info("Application startup complete")
    yield
    logger.info("Application shutting down")


app = FastAPI(title="Quiz App", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(basic_auth_middleware)

@app.get("/api/auth-check")
async def auth_check():
    return {"ok": True}

@app.get("/api/health")
async def health_check():
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}


app.include_router(documents.router, prefix="/api")
app.include_router(quizzes.router, prefix="/api")

static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
