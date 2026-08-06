# 文档下载功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给文档卡片加下载按钮——上传文档下载原始文件，粘贴文档导出为 `.txt`。

**Architecture:** 后端新增单一接口 `GET /api/documents/{id}/download`：`source_type == "upload"` 且文件存在时用 `FileResponse` 流式返回原文件（FastAPI 自动处理 RFC 5987 中文文件名）；`source_type == "paste"` 时返回 `text/plain` 的 content。前端在 DocumentCard 的 `.actions` 加一个图标链接（`download` 属性），无需走 emit 或 api.js。

**Tech Stack:** FastAPI + SQLAlchemy async；httpx `AsyncClient` 测试；Vue 3 SPA。

## Global Constraints

- 所有 API 路由已由全局 `basic_auth_middleware` 保护，新接口**不加任何认证逻辑**
- 禁止硬编码密钥/token/密码
- 测试沿用现有风格：`@pytest.mark.asyncio` + `AsyncClient(transport=ASGITransport(app=app))` + `BasicAuth`（见 `test_documents_api.py`）
- 中文/非 ASCII 文件名必须按 RFC 5987 用 `filename*=UTF-8''...` 编码，否则 latin-1 编码 headers 会抛 `UnicodeEncodeError`
- 上传文档磁盘文件名是 `{uuid}{ext}`，下载名统一用 `doc.title`（上传时 title 即原始文件名）
- 参考 spec：`docs/superpowers/specs/2026-08-06-document-download-design.md`

---

### Task 1: 后端下载接口（TDD）

**Files:**
- Modify: `backend/routers/documents.py`（新增接口 + import；`os` 已导入）
- Modify: `backend/tests/conftest.py`（加 `UPLOAD_DIR` 环境变量）
- Modify: `backend/tests/test_documents_api.py`（新增 3 条测试）

**Interfaces:**
- Consumes: 现有 `Document` 模型（字段 `id/title/source_type/file_path/content`）、`get_db` 依赖、`UPLOAD_DIR` from `backend.config`
- Produces: `GET /api/documents/{doc_id}/download` 接口——上传文档返回原文件字节，粘贴文档返回 `text/plain; charset=utf-8` 的 content；文档不存在或文件缺失返回 404

- [ ] **Step 1: conftest.py 增加 UPLOAD_DIR**

在 `backend/tests/conftest.py` 中、`DATABASE_URL` 设置之后追加（保持 `os.environ.setdefault` 风格）：

```python
os.environ.setdefault(
    "UPLOAD_DIR",
    str(PROJECT_ROOT / "data" / "uploads"),
)
```

这样上传测试把文件写到项目内 `data/uploads/`，而不是 Docker 默认的 `/app/data/uploads`。

- [ ] **Step 2: 写 3 条失败测试**

在 `backend/tests/test_documents_api.py` 末尾追加。顶部已有 import `os`，还需在文件顶部加 `from urllib.parse import unquote`（若已有则跳过）：

```python
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
```

- [ ] **Step 3: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/test_documents_api.py -v`

Expected: 3 条新测试 FAIL（`404` 或接口不存在），原有测试 PASS。

- [ ] **Step 4: 实现下载接口**

在 `backend/routers/documents.py` 顶部 import 区追加：

```python
import re
from urllib.parse import quote
from fastapi.responses import FileResponse, Response
```

在 `delete_document` 之后追加：

```python
@router.get("/documents/{doc_id}/download")
async def download_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    if doc.source_type == "upload" and doc.file_path and os.path.exists(doc.file_path):
        return FileResponse(doc.file_path, filename=doc.title)

    if doc.source_type == "paste":
        safe_name = re.sub(r'[\\/"]', "", doc.title).strip() or "document"
        if not safe_name.lower().endswith(".txt"):
            safe_name += ".txt"
        ascii_name = safe_name.encode("ascii", "ignore").decode() or "document.txt"
        disposition = (
            f'attachment; filename="{ascii_name}"; '
            f"filename*=UTF-8''{quote(safe_name)}"
        )
        return Response(
            content=doc.content,
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": disposition},
        )

    raise HTTPException(404, "No downloadable content")
```

关键点：
- `FileResponse(filename=doc.title)` 由 FastAPI 内部生成合法的 Content-Disposition（含 `filename*`），中文名安全
- paste 分支手工拼 header 时必须百分号编码（`quote`）非 ASCII 名，否则 Starlette 以 latin-1 编码 headers 时抛 `UnicodeEncodeError`
- `quote` 默认不编码 `/`，但 `safe_name` 已先剔除了 `\ / "`，无需额外处理
- 上传但磁盘文件已丢失 → 落入最后的 404

- [ ] **Step 5: 运行测试确认通过**

Run: `cd backend && python -m pytest tests/test_documents_api.py -v`

Expected: 全部 PASS（含新增 3 条）。

- [ ] **Step 6: 跑完整后端测试套件**

Run: `cd backend && python -m pytest tests/ -v`

Expected: 全部 PASS，无回归。

- [ ] **Step 7: 提交**

```bash
git add backend/routers/documents.py backend/tests/conftest.py backend/tests/test_documents_api.py
git commit -m "feat: add document download endpoint"
```

---

### Task 2: 前端下载图标按钮

**Files:**
- Modify: `frontend/src/components/DocumentCard.vue`

**Interfaces:**
- Consumes: 后端 `GET /api/documents/{doc_id}/download`（浏览器 Basic Auth 凭据已缓存，直接链接导航即可）
- Produces: 每个文档卡片 `.actions` 区新增下载图标链接，点击触发浏览器下载

- [ ] **Step 1: 添加下载图标链接**

在 `DocumentCard.vue` 模板的 `.actions` 区，`查看内容` 按钮之前插入：

```html
<a
  :href="'/api/documents/' + doc.id + '/download'"
  download
  class="btn-icon"
  title="下载"
  aria-label="下载"
>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="7 10 12 15 17 10"/>
    <line x1="12" y1="15" x2="12" y2="3"/>
  </svg>
</a>
```

- [ ] **Step 2: 添加 btn-icon 样式**

在 `DocumentCard.vue` 的 `<style scoped>` 内、`.actions` 规则之后追加（对齐 DocumentList 中 `close-btn` 的风格）：

```css
.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text-muted);
  padding: 6px;
  border-radius: var(--radius-sm);
  min-height: 32px;
  min-width: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
}

.btn-icon:hover {
  color: var(--color-text);
  background: var(--color-border-light);
}
```

`text-decoration: none` 避免 `<a>` 默认下划线；`display: inline-flex` + `align-items/justify-content` 让 SVG 居中。

- [ ] **Step 3: 前端构建验证**

Run: `cd frontend && npm run build`

Expected: 构建成功，无编译错误（Vite 会做模板编译检查）。

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/DocumentCard.vue
git commit -m "feat: add download icon button to document cards"
```

---

### Task 3: 手动端到端验证

**Files:** 无改动

- [ ] **Step 1: 启动服务**

Run: `./start_backend.sh`（需 `.env` 已存在，含 `DEEPSEEK_API_KEY` / `BASIC_AUTH_USER` / `BASIC_AUTH_PASS`）

- [ ] **Step 2: 验证上传文档下载**

浏览器打开首页 → 上传一个文件 → 点卡片上的下载图标 → 确认保存到本地、内容与原文件一致、文件名正确。

- [ ] **Step 3: 验证粘贴文档下载**

粘贴一篇文本创建文档 → 点下载图标 → 确认保存为 `<title>.txt`、内容一致。

- [ ] **Step 4: 验证移动端/窄屏布局**

窗口缩到 <480px，确认 `.actions` 区图标与按钮排列不溢出。

- [ ] **Step 5: 提交（若手动验证发现问题则修复后提交）**

无改动则跳过。
