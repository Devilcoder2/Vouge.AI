import os
from pathlib import Path
from dotenv import load_dotenv

# Load environmental variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    # Server configs
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # DB configs
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:postgres@localhost:5432/vouge"
    )
    DB_URL_SYNC: str = os.getenv(
        "DB_URL_SYNC", 
        "postgresql://postgres:postgres@localhost:5432/vouge"
    )
    
    # API Keys & Models
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    CLIP_MODEL_NAME: str = os.getenv("CLIP_MODEL_NAME", "openai/clip-vit-base-patch32")

    # JWT Authentication
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production-use-256-bit-secret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
    
    # Celery & Redis Background Processing
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    USE_CELERY: bool = os.getenv("USE_CELERY", "true").lower() == "true"
    
    # File storage configs
    UPLOAD_DIR: Path = BASE_DIR / os.getenv("UPLOAD_DIR", "uploads")
    PROCESSED_DIR: Path = BASE_DIR / os.getenv("PROCESSED_DIR", "processed")
    EMBEDDING_DIR: Path = BASE_DIR / os.getenv("EMBEDDING_DIR", "embeddings")
    PREVIEWS_DIR: Path = BASE_DIR / os.getenv("PREVIEWS_DIR", "previews")
    
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", "10485760")) # 10MB default
    ALLOWED_EXTENSIONS: set = set(
        os.getenv("ALLOWED_EXTENSIONS", "jpg,jpeg,png").lower().split(",")
    )

settings = Settings()

# Ensure standard operational folders exist locally
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
settings.EMBEDDING_DIR.mkdir(parents=True, exist_ok=True)
settings.PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)
