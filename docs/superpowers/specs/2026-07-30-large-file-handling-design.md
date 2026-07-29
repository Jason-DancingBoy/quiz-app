# Large File Handling Design

## 背景

当前系统上传 50MB 大文件生成题目时存在以下问题：

| 问题 | 根因 | 影响 |
|------|------|------|
| 嵌入阶段过慢 | 20000+ chunk 过 CPU SentenceTransformer，1-3 分钟无进度 | 用户体验 |
| RAG 浪费 | 50MB 提取 10MB 文本 → 20K 嵌入 → 仅取 8 个 chunk(~4KB) | 覆盖度差 |
| 无超时 | background task 无 `asyncio.wait_for` | 可能永久挂起 |
| 内存峰值 | 全量文本拼接进 SQLite，全量 chunk 列表驻留内存 | OOM 风险 |
| ChromaDB 无清理 | 删除文档时只删 SQLite 和文件，向量索引残留 | 磁盘膨胀 |
| 进度颗粒粗 | 嵌入阶段只推一次消息，然后卡住 | 用户以为卡死 |

## 目标

- 小文件（<=500 chunk）：现有流程不变
- 大文件（>500 chunk）：可生成题目，速度快，不耗尽资源
- 所有场景：有超时保护，有清理机制，有细粒度进度

## 设计

### 1. 分层采样跳过嵌入

**分流逻辑（`_run_generation`）：**

```
chunks = parse_text(doc.content).chunks
if len(chunks) <= 500:
    → 走现有 RAG 嵌入路径（insert_chunks → query_for_quiz）
else:
    → 走分层采样路径（跳过 ChromaDB 嵌入）
```

**采样函数（`rag_service.py` 新增 `sample_chunks`）：**

- 输入：全部 chunk 列表，目标采样数 N=30
- 策略：将 chunk 按文档顺序均分成 N 个桶，每桶随机取一个 chunk
- 去重：与 `query_for_quiz` 相同的文本重叠去重逻辑
- 输出：list[str]，约 15-30 个均匀覆盖全文的 chunk

**为什么均匀采样适合出题：**
语义检索倾向于拉回最相似的 chunk，导致题目集中在少数热门话题。均匀采样天然保证题目覆盖文档不同位置。

**LLM 上下文：** 30 chunk × 500 字符 ≈ 15K 字符 ≈ 5K token，远在 DeepSeek 窗口内。

**配置化：** `config.py` 新增 `LARGE_DOC_CHUNK_THRESHOLD = 500` 和 `SAMPLING_BUCKETS = 30`。

### 2. 超时保护

**`_run_generation` 整体加 `asyncio.wait_for(..., timeout=300)`：**

- 5 分钟上限，对任何场景都充裕
- 超时后设置 quiz.status="failed"，progress="生成超时，请尝试上传较小的文件"
- SSE 流发送 error 事件后关闭

### 3. 嵌入进度回调

**`insert_chunks` 加 `progress_callback` 参数：**

```python
async def insert_chunks(document_id, chunks, progress_callback=None):
    for i, batch in enumerate(batches(chunks, 50)):
        col.add(batch)
        if progress_callback:
            await progress_callback(i * 50 + len(batch), len(chunks))
```

**`_run_generation` 传入 callback：**

```python
async def on_embed_progress(done, total):
    await _push_progress(quiz_id, f"构建知识索引 ({done}/{total} 块)...", ...)

await insert_chunks(doc.id, chunks, progress_callback=on_embed_progress)
```

### 4. 流式上传

Starlette 的 `UploadFile` 已是 `SpooledTemporaryFile`：超过 1MB 自动写入 `/tmp/` 临时文件，`file.read()` 从临时文件读而非内存。**上传阶段无需改动。**

大文本不构建全量 chunk 列表：采样路径下，用正则按段落边界扫描文档，直接在桶位置取段落，跳过 `chunk_text()` 的全量切分。

### 5. ChromaDB 清理

**`rag_service.py` 新增：**

```python
async def delete_chunks(document_id: int):
    col = _get_collection()
    col.delete(where={"doc_id": str(document_id)})
```

**`documents.py` 的 `DELETE /documents/{id}` 中调用：**

```python
await delete_chunks(doc_id)
```

### 6. 前端

后端 SSE 进度流已完整，前端 `QuizPage.vue` 已消费 SSE。后端进度消息细化后，前端自动获得更好的进度展示，无需额外改动。

## 改动文件清单

| 文件 | 改动 | 行数估计 |
|------|------|---------|
| `backend/config.py` | 新增 `LARGE_DOC_CHUNK_THRESHOLD`、`SAMPLING_BUCKETS` | 2 |
| `backend/services/rag_service.py` | 新增 `sample_chunks`、`delete_chunks`，`insert_chunks` 加 callback | ~50 |
| `backend/routers/quizzes.py` | `_run_generation`：分流逻辑、timeout、callback | ~40 |
| `backend/routers/documents.py` | 删除端点调用 `delete_chunks`，大文本不构建全量 chunk | ~15 |
| `backend/tests/test_rag_service.py` | 新增 `sample_chunks` 单测 | ~20 |

## 非目标

- 不改前端
- 不改 Docker 配置
- 不换嵌入模型
- 不做 Map-Reduce 摘要
- 不调整分块参数
