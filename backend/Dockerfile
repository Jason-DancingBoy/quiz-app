FROM python:3.11-slim

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/

ENV HF_HOME=/app/models
ENV DATABASE_URL=sqlite+aiosqlite:////app/data/quiz.db
ENV LIGHTRAG_DIR=/app/data/lightrag
ENV UPLOAD_DIR=/app/data/uploads
ENV STATIC_DIR=/app/static

RUN mkdir -p /app/data /app/models /app/static
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
