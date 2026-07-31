# Quiz App

AI-powered quiz generation from uploaded documents. FastAPI + Vue 3 + SQLite + ChromaDB.

## Prerequisites

- Python 3.11+ (tested with 3.12)
- Node.js (only if rebuilding frontend)
- DeepSeek API key

## Quick Start

```bash
# 1. Create .env
cat > .env <<EOF
DEEPSEEK_API_KEY=sk-xxx
BASIC_AUTH_USER=admin
BASIC_AUTH_PASS=quiz2026
EOF

# 2. Set up Python venv
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# 3. Download embedding model (~93 MB, Chinese)
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-zh-v1.5', cache_folder='./models')"

# 4. Build frontend (or copy pre-built static/ from another server)
cd frontend && npm install && npm run build && cd ..

# 5. Launch
./start_backend.sh
```

`start_backend.sh` auto-detects its own directory via `PROJECT_ROOT` — it works from any location without editing paths. All data directories (`data/`, `models/`, `static/`) are relative to the project root.

## Environment Variables

| Variable | Default (auto-derived) |
|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///$PROJECT_ROOT/data/quiz.db` |
| `CHROMA_PERSIST_DIR` | `$PROJECT_ROOT/data/chroma` |
| `UPLOAD_DIR` | `$PROJECT_ROOT/data/uploads` |
| `VAULT_DIR` | `${VAULT_DIR:-$PROJECT_ROOT/../vault}` |
| `STATIC_DIR` | `$PROJECT_ROOT/static` |
| `HF_HOME` | `$PROJECT_ROOT/models` |
| `DEEPSEEK_API_KEY` | **Required** — set in `.env` |
| `BASIC_AUTH_USER` / `BASIC_AUTH_PASS` | **Required** — set in `.env` |

Defaults in `backend/config.py` are Docker-oriented (`/app/...`) — use the variables above to override for local/systemd deployments.

## Migrating to Another Server

### Must copy (gitignored, not in repo)

| Path | Size | Notes |
|---|---|---|
| `.env` | — | API key + credentials |
| `data/quiz.db` | ~2 MB | SQLite database |
| `data/chroma/` | ~8 MB | Vector index (must match embedding model) |
| `data/uploads/` | varies | User-uploaded documents |
| `models/hub/` | ~93 MB | Embedding model cache — copy to avoid re-download |
| `static/` | ~2 MB | Built frontend (or rebuild with `npm run build`) |

### Do NOT copy

- `venv/` — recreate with `pip install -r backend/requirements.txt`
- `frontend/node_modules/` — recreate with `npm install`

### Deployment

- **Local / dev**: `./start_backend.sh` — self-contained, no path editing needed
- **Docker**: `docker compose up` — uses relative volume mounts, fully portable
- **systemd**: generate from `quiz-app.service.template` (see below)

### systemd service (auto-adapting)

`quiz-app.service.template` uses `{{PLACEHOLDER}}` syntax. When a user asks to set up systemd, Claude should:

1. Detect the project root from the current working directory
2. Detect the current user with `whoami`
3. Ask for `VAULT_DIR` (or default to `$PROJECT_ROOT/../vault`)
4. Replace all `{{PLACEHOLDERS}}` and write to `quiz-app.service`
5. Output the `systemctl` commands to install and start it

This is intentionally a manual trigger — systemd setup requires root and should never happen automatically.

## Architecture

```
upload doc → chunk → embed (bge-small-zh-v1.5) → ChromaDB
                         ↓
generate quiz → retrieve chunks → DeepSeek API → quiz
                         ↓
take quiz → evaluate answers → RAGAS metrics (optional)
```

- **Backend**: FastAPI async, SQLAlchemy + aiosqlite, ChromaDB with BGE embedding
- **Frontend**: Vue 3 SPA served as static files by FastAPI at `/`
- **LLM**: DeepSeek via OpenAI-compatible API (`deepseek-v4-pro`)
- **Embedding**: Local `BAAI/bge-small-zh-v1.5` via sentence-transformers (offline)

## Tests

```bash
cd backend
python -m pytest tests/ -v
```

RAGAS evaluation (requires `requirements-dev.txt`):
```bash
cd backend
python -m pytest tests/ragas_eval/ -v
```
