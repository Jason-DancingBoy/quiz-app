#!/bin/bash
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# Source environment variables from .env file
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

export DATABASE_URL="sqlite+aiosqlite:///$PROJECT_ROOT/data/quiz.db"
export LIGHTRAG_DIR="$PROJECT_ROOT/data/lightrag"
export CHROMA_PERSIST_DIR="$PROJECT_ROOT/data/chroma"
export UPLOAD_DIR="$PROJECT_ROOT/data/uploads"
export VAULT_DIR="${VAULT_DIR:-$PROJECT_ROOT/../vault}"
export STATIC_DIR="$PROJECT_ROOT/static"
export HF_ENDPOINT="https://hf-mirror.com"
export HF_HOME="$PROJECT_ROOT/models"

exec "$PROJECT_ROOT/venv/bin/uvicorn" backend.main:app --host 0.0.0.0 --port 9200
