import os

DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-v4-pro"

BASIC_AUTH_USER = os.environ["BASIC_AUTH_USER"]
BASIC_AUTH_PASS = os.environ["BASIC_AUTH_PASS"]

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:////app/data/quiz.db")
LIGHTRAG_DIR = os.environ.get("LIGHTRAG_DIR", "/app/data/lightrag")
CHROMA_PERSIST_DIR = os.environ.get("CHROMA_PERSIST_DIR", "/app/data/chroma")
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/app/data/uploads")
VAULT_DIR = os.environ.get("VAULT_DIR", "/root/learning/vault")

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".md", ".txt"}
DAILY_QUOTA = 50
LARGE_DOC_CHUNK_THRESHOLD = 500  # chunks — skip embedding if total exceeds this
SAMPLING_BUCKETS = 30            # stratified buckets for large-doc sampling

STATIC_DIR = os.environ.get("STATIC_DIR", "/app/static")

# HuggingFace offline mode — use local model cache, skip network
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_HOME", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models")))
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
