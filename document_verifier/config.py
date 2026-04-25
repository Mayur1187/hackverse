import os
import tempfile
from pathlib import Path


def _load_local_env(base_dir: Path):
    env_path = base_dir / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    _load_local_env(BASE_DIR)

    IS_VERCEL = bool(os.getenv("VERCEL"))
    RUNTIME_DIR = Path(os.getenv("RUNTIME_DIR", Path(tempfile.gettempdir()) / "hactiverse" if IS_VERCEL else BASE_DIR))

    STORAGE_DIR = Path(os.getenv("STORAGE_DIR", RUNTIME_DIR / "storage"))
    UPLOAD_DIR = STORAGE_DIR / "uploads"
    PROCESSED_DIR = STORAGE_DIR / "processed"
    SAMPLE_DIR = STORAGE_DIR / "samples"
    INSTANCE_DIR = Path(os.getenv("INSTANCE_DIR", RUNTIME_DIR / "instance"))
    MODEL_DIR = Path(os.getenv("MODEL_DIR", RUNTIME_DIR / "models" if IS_VERCEL else BASE_DIR / "models"))
    DOCUMENT_TAMPER_MODEL_PATH = Path(os.getenv("DOCUMENT_TAMPER_MODEL_PATH", MODEL_DIR / "document_tamper_model.joblib"))
    DOCUMENT_TAMPER_MODEL_THRESHOLD = float(os.getenv("DOCUMENT_TAMPER_MODEL_THRESHOLD", "0.65"))

    # YOLO (Ultralytics): set to a local .pt path or hub id (e.g. yolov8n.pt). Empty = disabled.
    DOCUMENT_YOLO_MODEL = os.getenv("DOCUMENT_YOLO_MODEL", "").strip()
    DOCUMENT_YOLO_CONF = float(os.getenv("DOCUMENT_YOLO_CONF", "0.35"))
    DOCUMENT_YOLO_MAX_DET = int(os.getenv("DOCUMENT_YOLO_MAX_DET", "32"))

    SECRET_KEY = os.getenv("SECRET_KEY", "local-hackathon-secret")
    @staticmethod
    def _resolve_database_uri(default_uri: str) -> str:
        database_url = os.getenv("DATABASE_URL", "").strip()
        if not database_url:
            return default_uri
        # Some providers still emit postgres:// URLs, but SQLAlchemy expects postgresql://.
        if database_url.startswith("postgres://"):
            return database_url.replace("postgres://", "postgresql://", 1)
        return database_url

    SQLALCHEMY_DATABASE_URI = _resolve_database_uri.__func__(f"sqlite:///{INSTANCE_DIR / 'verifier.sqlite3'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024

    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "tif", "tiff", "pdf"}

    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
    GROQ_TIMEOUT_SECONDS = int(os.getenv("GROQ_TIMEOUT_SECONDS", "20"))

    @classmethod
    def ensure_directories(cls):
        for path in (cls.UPLOAD_DIR, cls.PROCESSED_DIR, cls.SAMPLE_DIR, cls.INSTANCE_DIR, cls.MODEL_DIR):
            path.mkdir(parents=True, exist_ok=True)
