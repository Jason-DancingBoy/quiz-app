# 文档下载功能设计

日期：2026-08-06
状态：已批准

## 目标

为文档列表中的每个文档提供「下载」能力：
- **上传文档**（source_type = upload）→ 下载原始上传文件（PDF/Word/PPT/MD/TXT）
- **粘贴文档**（source_type = paste）→ 导出 content 为 `.txt`

## 方案选型

采用**方案 A：单一下载接口**。对比：
- A：一个接口处理两种情形，前端加一个图标按钮，改动最小
- B：下载/导出拆两个接口，职责更清晰但复杂度更高，当前场景无收益
- C：前端 fetch blob 下载，与 api.js 401 逻辑一致但需解析文件名，过度设计

## 后端设计

文件：`backend/routers/documents.py`，新增一个接口：

```python
@router.get("/documents/{doc_id}/download")
async def download_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    if doc.source_type == "upload" and doc.file_path and os.path.exists(doc.file_path):
        return FileResponse(doc.file_path, filename=doc.title)
    if doc.source_type == "paste":
        headers = {"Content-Disposition": f'attachment; filename="{safe_name}"'}
        return Response(content=doc.content, media_type="text/plain; charset=utf-8", headers=headers)

    raise HTTPException(404, "No downloadable content")
```

### 设计要点

- **文件名安全**：上传文档的 `doc.title` 取自用户上传的 `file.filename`，可能含非法字符。`FileResponse(filename=...)` 由 FastAPI 自动处理 Content-Disposition 转义（中文用 `filename*`）。粘贴文档的 `.txt` 文件名需在服务端 sanitize（去除 `/\` 等路径分隔符），防止 header 注入
- **粘贴文件名规则**：`safe_name = re.sub(r'[\\/"]', '', doc.title)`，若为空则回退 `"document"`；再确保 `.txt` 后缀——若 sanitize 后已以 `.txt` 结尾则不再追加，否则追加 `.txt`。写入 `Content-Disposition: attachment; filename="..."`
- **路径安全**：`doc.file_path` 由 upload 接口生成（`UPLOAD_DIR/{uuid}{ext}`），不存在用户可控目录穿越
- **流式返回**：用 `FileResponse` 而非全量 `read()`，大文件不占内存
- **边界情况**：上传记录但磁盘文件已不存在（极少数）→ 落入 404
- **认证**：`basic_auth_middleware` 是全局 HTTP 中间件，新接口自动受 Basic Auth 保护，无需额外处理

### 新增导入

`backend/routers/documents.py` 顶部增加 `from fastapi.responses import FileResponse, Response`。

## 前端设计

文件：`frontend/src/components/DocumentCard.vue`，在 `.actions` 区新增图标下载链接：

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

### 设计要点

- **图标风格**：对齐项目现有 SVG（`viewBox 24`、`stroke currentColor`、`width/height 20`），下载箭头图标
- **为何用链接而非 emit**：现有按钮（查看/生成/删除）需父组件逻辑，而下载只需一个 GET 链接。浏览器 Basic Auth 凭据已缓存，点击即下载，`Content-Disposition` 带正确文件名，无需走 emit 再绕一层
- **`download` 属性**：同源 URL 下以附件方式保存，不离开页面
- **`btn-icon` 样式**：参考现有 `close-btn` 风格（透明背景、hover 变灰、圆角、32px 点击区），新增样式类到 scoped style
- **`title` + `aria-label`**：图标无文字，补无障碍/悬停提示
- **零改动**：`api.js` 与 `DocumentList.vue` 不需要改；粘贴文档同样显示下载按钮，前端无需区分 source_type

## 测试

### 后端（`backend/tests/test_documents_api.py` 新增 3 条）

1. 上传文件 → GET `/api/documents/{id}/download` → 200，响应体与原文件一致，Content-Disposition 带原始文件名
2. 粘贴文档 → GET `/api/documents/{id}/download` → 200，`text/plain`，响应体 = content
3. 不存在的 id → 404

### 前端

项目无前端测试框架，手动验证：`npm run build` + `./start_backend.sh`，分别点上传文档与粘贴文档的下载按钮，确认文件保存到本地且内容正确。

## 改动文件清单

| 文件 | 改动 |
|---|---|
| `backend/routers/documents.py` | 新增 `download_document` 接口 + 2 个 import |
| `backend/tests/test_documents_api.py` | 新增 3 条测试 |
| `frontend/src/components/DocumentCard.vue` | `.actions` 加图标下载链接 + `btn-icon` 样式 |
