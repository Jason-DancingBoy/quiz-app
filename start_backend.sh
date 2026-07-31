#!/bin/bash
cd /home/jason/learning/quiz-app

# Source environment variables from .env file
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

export DATABASE_URL="sqlite+aiosqlite:////home/jason/learning/quiz-app/data/quiz.db"
export LIGHTRAG_DIR="/home/jason/learning/quiz-app/data/lightrag"
export CHROMA_PERSIST_DIR="/home/jason/learning/quiz-app/data/chroma"
export UPLOAD_DIR="/home/jason/learning/quiz-app/data/uploads"
export VAULT_DIR="/home/jason/learning/vault"
export STATIC_DIR="/home/jason/learning/quiz-app/static"
export HF_ENDPOINT="https://hf-mirror.com"
export HF_HOME="/home/jason/learning/quiz-app/models"

exec /home/jason/learning/quiz-app/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 9200
