# Large File Handling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add guardrails for large file uploads (>500 chunks): stratified sampling bypasses slow embedding, 5-minute timeout prevents hangs, progress callback gives real-time feedback, ChromaDB cleanup on document delete.

**Architecture:** Four changes to the generation pipeline: (1) config knob for the chunk threshold; (2) `rag_service` gets `sample_chunks()` for embedding-free stratified sampling, `delete_chunks()` for cleanup, and a `progress_callback` on `insert_chunks`; (3) `_run_generation` branches on chunk count — <=500 unchanged, >500 samples instead of embedding — and wraps everything in `asyncio.wait_for`; (4) `DELETE /documents/{id}` calls `delete_chunks`. Frontend and Docker config are untouched.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy async, ChromaDB, sentence-transformers, asyncio

## Global Constraints

- Small files (<=500 chunks): existing RAG embedding path is unchanged
- Large files (>500 chunks): skip ChromaDB embedding, use `sample_chunks()` instead
- `LARGE_DOC_CHUNK_THRESHOLD = 500`, `SAMPLING_BUCKETS = 30` in config.py
- 5-minute `asyncio.wait_for` timeout on entire `_run_generation`
- No frontend changes, no Docker changes, no model changes

---

### Task 1: Add config constants

**Files:**
- Modify: `backend/config.py`

**Interfaces:**
- Produces: `LARGE_DOC_CHUNK_THRESHOLD: int = 500`, `SAMPLING_BUCKETS: int = 30`

- [ ] **Step 1: Add the two config constants**

In `backend/config.py`, after `DAILY_QUOTA = 50` (line 18):

```python
LARGE_DOC_CHUNK_THRESHOLD = 500  # chunks — skip embedding if total exceeds this
SAMPLING_BUCKETS = 30            # stratified buckets for large-doc sampling
```

- [ ] **Step 2: Verify config imports cleanly**

Run: `cd /home/jason/learning/quiz-app && python -c "from backend.config import LARGE_DOC_CHUNK_THRESHOLD, SAMPLING_BUCKETS; print(LARGE_DOC_CHUNK_THRESHOLD, SAMPLING_BUCKETS)"`
Expected: `500 30`

- [ ] **Step 3: Commit**

```bash
cd /home/jason/learning/quiz-app
git add backend/config.py
git commit -m "feat: add large-doc chunk threshold and sampling bucket config

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 2: Add sample_chunks, delete_chunks, and progress_callback to rag_service

**Files:**
- Modify: `backend/services/rag_service.py`
- Create: `backend/tests/test_rag_service.py`

**Interfaces:**
- Consumes: `LARGE_DOC_CHUNK_THRESHOLD`, `SAMPLING_BUCKETS` from `backend.config`
- Produces:
  - `async def sample_chunks(chunks: list[str], n_buckets: int = SAMPLING_BUCKETS) -> list[str]`
  - `async def delete_chunks(document_id: int) -> None`
  - `async def insert_chunks(document_id: int, chunks: list[str], progress_callback: Callable[[int, int], Awaitable[None]] | None = None) -> None` (modified signature)

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_rag_service.py`:

```python
import pytest
from backend.services.rag_service import sample_chunks, delete_chunks, insert_chunks


class TestSampleChunks:
    def test_short_input_returns_all(self):
        chunks = [f"chunk {i}" for i in range(10)]
        result = sample_chunks(chunks, n_buckets=30)
        assert len(result) == 10

    def test_large_input_samples_down(self):
        chunks = [f"chunk {i} unique content {i} " * 5 for i in range(1000)]
        result = sample_chunks(chunks, n_buckets=30)
        assert 15 <= len(result) <= 30

    def test_coverage_spans_entire_document(self):
        """Stratified sampling should pick chunks from across the full range."""
        chunks = [f"section {i:04d}" for i in range(1000)]
        result = sample_chunks(chunks, n_buckets=30)
        indices = [chunks.index(r) for r in result]
        # At least one chunk from first third and one from last third
        assert any(i < 333 for i in indices), "no chunk from first third"
        assert any(i > 666 for i in indices), "no chunk from last third"

    def test_overlap_dedup_removes_duplicates(self):
        chunks = ["the quick brown fox jumps over the lazy dog"] * 100
        result = sample_chunks(chunks, n_buckets=10)
        assert len(result) == 1

    def test_empty_input(self):
        assert sample_chunks([], n_buckets=30) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/jason/learning/quiz-app && python -m pytest backend/tests/test_rag_service.py -v`
Expected: FAIL — `sample_chunks` not defined, `delete_chunks` not defined

- [ ] **Step 3: Implement `sample_chunks` in rag_service.py**

Add after `_chunks_overlap` function (after line 89) in `backend/services/rag_service.py`:

```python
import random

from backend.config import SAMPLING_BUCKETS


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
```

- [ ] **Step 4: Run tests to verify sample_chunks passes**

Run: `cd /home/jason/learning/quiz-app && python -m pytest backend/tests/test_rag_service.py::TestSampleChunks -v`
Expected: all 5 pass

- [ ] **Step 5: Implement `delete_chunks` in rag_service.py**

Add after `insert_chunks` function:

```python
async def delete_chunks(document_id: int) -> None:
    """Remove all embedded chunks for a document from ChromaDB."""
    col = _get_collection()
    col.delete(where={"doc_id": str(document_id)})
    logger.info("Chunks deleted from ChromaDB: doc_id=%d", document_id)
```

- [ ] **Step 6: Modify `insert_chunks` to accept progress_callback**

Replace the existing `insert_chunks` function (lines 43-53) with:

```python
import asyncio
from collections.abc import Awaitable, Callable


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
```

- [ ] **Step 7: Run all tests**

Run: `cd /home/jason/learning/quiz-app && python -m pytest backend/tests/test_rag_service.py -v`
Expected: all pass

- [ ] **Step 8: Commit**

```bash
cd /home/jason/learning/quiz-app
git add backend/services/rag_service.py backend/tests/test_rag_service.py
git commit -m "feat: add sample_chunks, delete_chunks, and insert_chunks progress callback

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 3: Add branching logic, timeout, and progress callback to quiz generation

**Files:**
- Modify: `backend/routers/quizzes.py`

**Interfaces:**
- Consumes:
  - `LARGE_DOC_CHUNK_THRESHOLD` from `backend.config`
  - `sample_chunks` from `backend.services.rag_service` (Task 2)
  - `insert_chunks` updated signature from Task 2
- Produces: no new public interfaces

- [ ] **Step 1: Update imports in quizzes.py**

In `backend/routers/quizzes.py`, update the config import (line 16) to include the new constants:

```python
from backend.config import VAULT_DIR, LARGE_DOC_CHUNK_THRESHOLD
```

And update the rag_service import (line 18) to include `sample_chunks`:

```python
from backend.services.rag_service import insert_chunks, query_for_quiz, sample_chunks
```

- [ ] **Step 2: Replace the RAG section in `_run_generation` with branching logic**

Replace lines 194-219 in `backend/routers/quizzes.py` (from `chunks = parse_text(doc.content).chunks` through the `knowledge = await query_for_quiz(...)` line) with:

```python
            chunks = parse_text(doc.content).chunks
            logger.info("Generation progress (quiz_id=%d): %d chunks created", quiz_id, len(chunks))

            total_chunk_text = "".join(chunks)
            SHORT_DOC_THRESHOLD = 6000  # chars — skip RAG if total content fits easily in LLM context

            if len(total_chunk_text) <= SHORT_DOC_THRESHOLD:
                quiz.progress = "文档较短，跳过检索..."
                await db.commit()
                await _push_progress(quiz_id, "文档较短，跳过检索...", 0, count)
                knowledge = total_chunk_text
                logger.info("Generation progress (quiz_id=%d): short doc (%d chars), skipping RAG", quiz_id, len(knowledge))
            elif len(chunks) <= LARGE_DOC_CHUNK_THRESHOLD:
                quiz.progress = f"构建知识索引 ({len(chunks)} 块)..."
                await db.commit()
                await _push_progress(quiz_id, f"构建知识索引 ({len(chunks)} 块)...", 0, count)

                async def _embed_progress(done, total):
                    await _push_progress(quiz_id, f"构建知识索引 ({done}/{total} 块)...", 0, count)

                await insert_chunks(doc.id, chunks, progress_callback=_embed_progress)
                logger.info("Generation progress (quiz_id=%d): embeddings inserted", quiz_id)

                quiz.progress = "检索关键知识点..."
                await db.commit()
                await _push_progress(quiz_id, "检索关键知识点...", 0, count)

                knowledge = await query_for_quiz(doc.id, difficulty, chunks)
                logger.info("Generation progress (quiz_id=%d): knowledge retrieved (%d chars)", quiz_id, len(knowledge))
            else:
                quiz.progress = f"文档较大 ({len(chunks)} 块)，均匀采样中..."
                await db.commit()
                await _push_progress(quiz_id, f"文档较大 ({len(chunks)} 块)，均匀采样中...", 0, count)

                sampled = sample_chunks(chunks)
                knowledge = "\n\n".join(sampled)
                logger.info("Generation progress (quiz_id=%d): %d chunks sampled to %d (no embedding)", quiz_id, len(chunks), len(sampled))
```

- [ ] **Step 3: Wrap `_run_generation` body in `asyncio.wait_for`**

Wrap the entire body inside `async with async_session() as db:` try block (from `try:` on line 186 to the `except` on line 291) with `asyncio.wait_for`. The cleanest approach: add a helper async function `_do_generate` and call it with `wait_for`.

Add this helper function just before `_run_generation` (before line 177).

**How to build `_do_generate`:** Copy the entire body of the current `_run_generation` function starting from `from backend.database import async_session` (original line 178) through the end of the try/except block (original line 298), with these changes:
- Remove the `queue = asyncio.Queue()` and `_stream_queues[quiz_id] = queue` lines (those stay in `_run_generation`)
- Remove all `_stream_queues.pop(quiz_id, None)` calls (cleanup is handled by `_run_generation`'s `finally` block)
- Replace `await queue.put(...)` with `q = _stream_queues.get(quiz_id); if q: await q.put(...)`

Result should be:

```python
async def _do_generate(quiz_id: int, doc: Document, difficulty: str, count: int):
    from backend.database import async_session
    async with async_session() as db:
        try:
            quiz = await db.get(Quiz, quiz_id)

            quiz.progress = "切分文档..."
            await db.commit()
            await _push_progress(quiz_id, "切分文档...", 0, count)

            chunks = parse_text(doc.content).chunks
            # ... (Step 2's branching logic replaces the RAG section here) ...
            # ... (rest of existing logic: segments, parallel gen, collect results) ...

            # All done — use _stream_queues.get() instead of local queue variable
            quiz.status = "ready"
            quiz.progress = None
            await db.commit()
            increment_quota()
            q = _stream_queues.get(quiz_id)
            if q:
                await q.put({"type": "done", "generated_count": count, "total_count": count})

        except Exception as e:
            logger.error("Background generation failed: quiz_id=%d error=%s", quiz_id, e)
            quiz = await db.get(Quiz, quiz_id)
            if quiz:
                quiz.status = "failed"
                quiz.progress = f"生成失败: {str(e)[:200]}"
                await db.commit()
            q = _stream_queues.get(quiz_id)
            if q:
                await q.put({"type": "error", "message": str(e)[:200]})
```

Then replace `_run_generation` with:

```python
async def _run_generation(quiz_id: int, doc: Document, difficulty: str, count: int):
    logger.info("Background generation started: quiz_id=%d difficulty=%s count=%d", quiz_id, difficulty, count)

    queue = asyncio.Queue()
    _stream_queues[quiz_id] = queue

    try:
        await asyncio.wait_for(
            _do_generate(quiz_id, doc, difficulty, count),
            timeout=300,
        )
    except asyncio.TimeoutError:
        logger.error("Background generation timed out: quiz_id=%d", quiz_id)
        from backend.database import async_session
        async with async_session() as db:
            quiz = await db.get(Quiz, quiz_id)
            if quiz:
                quiz.status = "failed"
                quiz.progress = "生成超时，请尝试上传较小的文件"
                await db.commit()
        q = _stream_queues.get(quiz_id)
        if q:
            await q.put({"type": "error", "message": "生成超时，请尝试上传较小的文件"})
    finally:
        _stream_queues.pop(quiz_id, None)
```

Note: the `_stream_queues.pop(quiz_id, None)` calls inside `_do_generate`'s except block should be removed — the `finally` block in `_run_generation` handles cleanup. The done/success path in `_do_generate` also doesn't need to pop since the `finally` handles it.

- [ ] **Step 4: Run existing tests to verify no regressions**

Run: `cd /home/jason/learning/quiz-app && python -m pytest backend/tests/test_quizzes_api.py -v`
Expected: all pass (no regressions in quiz API)

- [ ] **Step 5: Commit**

```bash
cd /home/jason/learning/quiz-app
git add backend/routers/quizzes.py
git commit -m "feat: add large-doc sampling branch, 5min timeout, and embed progress callback

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 4: Add ChromaDB cleanup to document delete endpoint

**Files:**
- Modify: `backend/routers/documents.py`

**Interfaces:**
- Consumes: `delete_chunks` from `backend.services.rag_service` (Task 2)

- [ ] **Step 1: Add import for delete_chunks**

In `backend/routers/documents.py`, update the import line (currently line 12):

```python
from backend.services.parser import parse_text, parse_file, PARSERS
```

Add after it:

```python
from backend.services.rag_service import delete_chunks
```

- [ ] **Step 2: Call delete_chunks in the delete endpoint**

In `delete_document` (line 134), add `await delete_chunks(doc_id)` after the file cleanup block (after line 155, before `await db.commit()`):

```python
    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)
        logger.info("Deleted uploaded file: %s", doc.file_path)

    await delete_chunks(doc_id)

    await db.commit()
```

- [ ] **Step 3: Run document API tests**

Run: `cd /home/jason/learning/quiz-app && python -m pytest backend/tests/test_documents_api.py -v`
Expected: all pass

- [ ] **Step 4: Commit**

```bash
cd /home/jason/learning/quiz-app
git add backend/routers/documents.py
git commit -m "feat: clean up ChromaDB chunks on document delete

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 5: Run full test suite and verify

- [ ] **Step 1: Run the full test suite**

```bash
cd /home/jason/learning/quiz-app && python -m pytest backend/tests/ -v
```

Expected: all tests pass, no regressions.

- [ ] **Step 2: Run a manual smoke test with a small file (optional — requires running server)**

```bash
# Start the backend server in Docker
cd /home/jason/learning/quiz-app && docker-compose up -d

# Create a test document via paste API
curl -X POST http://localhost:8000/api/documents \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n test:test | base64)" \
  -d '{"title": "smoke test", "content": "The mitochondria is the powerhouse of the cell. It converts glucose into ATP through cellular respiration. The process involves glycolysis, the Krebs cycle, and the electron transport chain."}'

# Generate quiz (replace {doc_id} with the returned id)
curl -X POST http://localhost:8000/api/documents/{doc_id}/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n test:test | base64)" \
  -d '{"difficulty": "easy", "question_count": 2}'

# Check quiz status
curl http://localhost:8000/api/quizzes/{quiz_id} \
  -H "Authorization: Basic $(echo -n test:test | base64)"

# Delete document
curl -X DELETE http://localhost:8000/api/documents/{doc_id} \
  -H "Authorization: Basic $(echo -n test:test | base64)"
```
