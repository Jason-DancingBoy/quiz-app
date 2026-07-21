import os
import asyncio

from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc
from sentence_transformers import SentenceTransformer

from backend.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, LIGHTRAG_DIR


_rag_instance: LightRAG | None = None
_model_lock = asyncio.Lock()


async def _get_embedding_model():
    model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
    return model


async def _embedding_func(texts: list[str]) -> list[list[float]]:
    model = await _get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


async def _llm_func(prompt: str, system_prompt: str | None = None, **kwargs) -> str:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    response = await client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=messages,
        temperature=0.3,
    )
    return response.choices[0].message.content


async def get_rag(document_id: int) -> LightRAG:
    global _rag_instance
    async with _model_lock:
        if _rag_instance is None:
            working_dir = os.path.join(LIGHTRAG_DIR, str(document_id))
            os.makedirs(working_dir, exist_ok=True)
            _rag_instance = LightRAG(
                working_dir=working_dir,
                llm_model_func=_llm_func,
                embedding_func=EmbeddingFunc(
                    embedding_dim=384,
                    max_token_size=512,
                    func=_embedding_func,
                ),
            )
            await _rag_instance.initialize_storages()
    return _rag_instance


async def insert_chunks(document_id: int, chunks: list[str]):
    rag = await get_rag(document_id)
    for i, chunk in enumerate(chunks):
        await rag.ainsert(chunk, ids=f"chunk_{i}")


async def query_for_quiz(document_id: int, difficulty: str) -> str:
    rag = await get_rag(document_id)

    mode_map = {"easy": "local", "medium": "hybrid", "hard": "global"}
    mode = mode_map.get(difficulty, "hybrid")

    query_text = "适合出题的关键知识点和重要概念"
    result = await rag.aquery(query_text, param=QueryParam(mode=mode))
    return result


def reset_rag():
    global _rag_instance
    _rag_instance = None
