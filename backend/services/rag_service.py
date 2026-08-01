import asyncio
import os
import random

from collections.abc import Awaitable, Callable

import chromadb
from chromadb.utils import embedding_functions

from backend.config import CHROMA_PERSIST_DIR, SAMPLING_BUCKETS
from backend.logger import get_logger

# Imported after config to pick up HF_HUB_OFFLINE / HF_HOME env vars
from sentence_transformers import SentenceTransformer

logger = get_logger(__name__)

_client = None
_collection = None


class BgeEmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __init__(self, model_path: str):
        self._model = SentenceTransformer(model_path)

    def name(self) -> str:
        return "bge-small-zh-v1.5"

    def __call__(self, input: list[str]) -> list[list[float]]:
        return self._model.encode(input, normalize_embeddings=True).tolist()


def _get_collection():
    global _client, _collection
    if _collection is None:
        model_path = os.environ.get("EMBEDDING_MODEL_PATH", "BAAI/bge-small-zh-v1.5")
        _client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        _collection = _client.get_or_create_collection(
            name="doc_chunks",
            embedding_function=BgeEmbeddingFunction(model_path),
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB collection initialized: %d documents", _collection.count())
    return _collection


async def insert_chunks(
    document_id: int,
    chunks: list[str],
    progress_callback: Callable[[int, int], Awaitable[None]] | None = None,
) -> None:
    if not chunks:
        return
    logger.info("Upserting %d chunks for doc_id=%d", len(chunks), document_id)
    col = _get_collection()
    col.delete(where={"doc_id": str(document_id)})

    batch_size = 50
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        col.add(
            ids=[f"doc{document_id}_chunk{j}" for j in range(i, i + len(batch))],
            documents=batch,
            metadatas=[{"doc_id": str(document_id)}] * len(batch),
        )
        done = i + len(batch)
        if progress_callback:
            await progress_callback(done, len(chunks))

    logger.info("Chunks upserted: doc_id=%d chunks=%d", document_id, len(chunks))


async def delete_chunks(document_id: int) -> None:
    """Remove all embedded chunks for a document from ChromaDB."""
    col = _get_collection()
    await asyncio.to_thread(col.delete, where={"doc_id": str(document_id)})
    logger.info("Chunks deleted from ChromaDB: doc_id=%d", document_id)


DIFFICULTY_HINTS = {
    "easy": "基础概念 定义 是什么 特征 分类 概述",
    "medium": "原因 过程 关系 对比 区别 应用 原理 为什么",
    "hard": "例外 前提 局限 边界条件 反例 隐含假设 深层原因 细微差异",
}


def _build_query_from_chunks(chunks: list[str], difficulty: str) -> str:
    """Build a difficulty-aware retrieval query with uniform topic coverage."""
    if not chunks:
        return ""

    hint = DIFFICULTY_HINTS.get(difficulty, DIFFICULTY_HINTS["medium"])

    samples = []
    n = len(chunks)
    step = max(1, n // 4)
    for i in range(0, n, step):
        text = chunks[i][:250]
        first_period = max(text.find("。"), text.find("！"), text.find("？"))
        if first_period > 50:
            text = text[:first_period + 1]
        samples.append(text)
        if len(samples) >= 4:
            break

    return hint + " " + " ".join(samples)


def _chunks_overlap(a: str, b: str, min_overlap: int = 80) -> bool:
    if len(a) < min_overlap or len(b) < min_overlap:
        return False
    return a[:min_overlap] in b or b[:min_overlap] in a


def sample_chunks(chunks: list[str], n_buckets: int = SAMPLING_BUCKETS) -> list[str]:
    """Stratified random sampling: divide chunks into n_buckets, pick one random chunk per bucket,
    then deduplicate by text overlap.  Returns 15-30 evenly-distributed chunks covering the full doc."""
    if not chunks:
        return []

    if len(chunks) <= n_buckets:
        # Deduplicate directly
        unique = []
        for c in chunks:
            if not any(_chunks_overlap(c, existing) for existing in unique):
                unique.append(c)
        return unique

    bucket_size = len(chunks) // n_buckets
    sampled = []
    for i in range(n_buckets):
        start = i * bucket_size
        end = start + bucket_size if i < n_buckets - 1 else len(chunks)
        if start >= end:
            continue
        idx = random.randint(start, end - 1)
        sampled.append(chunks[idx])

    unique = []
    for c in sampled:
        if not any(_chunks_overlap(c, existing) for existing in unique):
            unique.append(c)

    return unique


async def query_for_quiz(document_id: int, difficulty: str, chunks: list[str] | None = None) -> str:
    col = _get_collection()
    all_docs = col.get(where={"doc_id": str(document_id)})
    if not all_docs["ids"]:
        return ""

    if chunks:
        query_text = _build_query_from_chunks(chunks, difficulty)
    else:
        query_text = "关键知识点 重要概念 核心内容"

    available = len(all_docs["ids"])
    fetch_count = min(15, available)

    result = col.query(
        query_texts=[query_text],
        n_results=fetch_count,
        where={"doc_id": str(document_id)},
    )

    documents = result.get("documents", [[]])[0]

    unique = []
    for doc in documents:
        if not any(_chunks_overlap(doc, existing) for existing in unique):
            unique.append(doc)
        if len(unique) >= 8:
            break

    logger.info("Retrieved %d chunks, deduplicated to %d (difficulty=%s)", len(documents), len(unique), difficulty)
    return "\n\n".join(unique)


async def warmup_embedding_model():
    """Preload the embedding model at app startup so first request is fast."""
    try:
        col = _get_collection()
        logger.info("Embedding model warmed up: %d documents in collection", col.count())
    except Exception as e:
        logger.warning("Embedding model warmup failed (non-fatal): %s", e)


def reset_rag():
    global _client, _collection
    if _client is not None:
        try:
            _client.delete_collection("doc_chunks")
        except Exception:
            pass
    _client = None
    _collection = None
    logger.info("ChromaDB collection reset")
