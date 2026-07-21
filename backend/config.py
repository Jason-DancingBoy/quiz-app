import os

DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-v4-pro"

BASIC_AUTH_USER = os.environ["BASIC_AUTH_USER"]
BASIC_AUTH_PASS = os.environ["BASIC_AUTH_PASS"]

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:////app/data/quiz.db")
LIGHTRAG_DIR = os.environ.get("LIGHTRAG_DIR", "/app/data/lightrag")
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/app/data/uploads")

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".md", ".txt"}
DAILY_QUOTA = 50

STATIC_DIR = os.environ.get("STATIC_DIR", "/app/static")
