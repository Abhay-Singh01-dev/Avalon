from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from dotenv import load_dotenv
from typing import Optional, List
import os
import secrets

# Load environment variables
load_dotenv()

def parse_cors_origins():
    """Parse CORS origins from environment or defaults."""
    cors_env = os.getenv("BACKEND_CORS_ORIGINS")
    if cors_env:
        return [i.strip() for i in cors_env.split(",") if i.strip()]
    return ["http://localhost:3000", "http://localhost:8000"]

class Settings(BaseSettings):
    # Basic App Data
    PROJECT_NAME: str = "Pharma AI Platform"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # API Config
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = parse_cors_origins()

    # MongoDB - LOCAL ONLY (no cloud/Atlas)
    # This application uses only local MongoDB instance
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "pharma_ai_db")

    # Authentication Config
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    ADMIN_EMAIL: Optional[str] = os.getenv("ADMIN_EMAIL")
    ADMIN_PASSWORD: Optional[str] = os.getenv("ADMIN_PASSWORD")

    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024
    ALLOWED_FILE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif", "application/pdf"]

    # External APIs & Integrations
    EXTERNAL_REQUEST_TIMEOUT: float = float(os.getenv("EXTERNAL_REQUEST_TIMEOUT", 15))
    EXTERNAL_MAX_RETRIES: int = int(os.getenv("EXTERNAL_MAX_RETRIES", 3))
    EXTERNAL_CACHE_TTL: int = int(os.getenv("EXTERNAL_CACHE_TTL", 60 * 60 * 24))  # 24h

    PUBMED_BASE_URL: str = os.getenv("PUBMED_BASE_URL", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils")
    PUBMED_RATE_LIMIT_RPS: float = float(os.getenv("PUBMED_RATE_LIMIT_RPS", 3))

    CLINICALTRIALS_BASE_URL: str = os.getenv(
        "CLINICALTRIALS_BASE_URL", "https://clinicaltrials.gov/api/query/study_fields"
    )
    CLINICALTRIALS_MAX_RECORDS: int = int(os.getenv("CLINICALTRIALS_MAX_RECORDS", 40))
    CLINICALTRIALS_CACHE_TTL: int = int(os.getenv("CLINICALTRIALS_CACHE_TTL", 60 * 60 * 24))

    PATENTSVIEW_BASE_URL: str = os.getenv("PATENTSVIEW_BASE_URL", "https://api.patentsview.org/patents/query")
    PATENTSVIEW_PAGE_SIZE: int = int(os.getenv("PATENTSVIEW_PAGE_SIZE", 20))
    PATENTSVIEW_CACHE_TTL: int = int(os.getenv("PATENTSVIEW_CACHE_TTL", 60 * 60 * 24))
    PATENTSVIEW_API_KEY: Optional[str] = os.getenv("PATENTSVIEW_API_KEY")

    IQVIA_API_KEY: Optional[str] = os.getenv("IQVIA_API_KEY")  # placeholder for future integrations

    # LLM Config (LM Studio)
    LMSTUDIO_MODEL_NAME: str = os.getenv("LMSTUDIO_MODEL_NAME", "mistral-7b-instruct-v0.3-q6_k")
    LMSTUDIO_MAX_TOKENS: int = int(os.getenv("LMSTUDIO_MAX_TOKENS", 4096))
    LMSTUDIO_TEMPERATURE: float = float(os.getenv("LMSTUDIO_TEMPERATURE", 0.2))
    
    # Cloud LLM Config (Placeholder - Not Active)
    CLOUD_ENABLED: bool = os.getenv("CLOUD_ENABLED", "false").lower() == "true"
    CLOUD_PROVIDER: str = os.getenv("CLOUD_PROVIDER", "claude")  # "claude" or "gpt"
    CLOUD_API_KEY: str = os.getenv("CLOUD_API_KEY", "")

    # Email (optional)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None

    # Rate Limit
    RATE_LIMIT_PER_MINUTE: int = 100

    # Session Security
    SECURE_COOKIES: bool = False
    SESSION_COOKIE_NAME: str = "session"

    # ============================================
    # PROJECT RAG FEATURE FLAGS (DISABLED BY DEFAULT)
    # These features require larger models (≥14B/70B)
    # Current local model (Mistral 7B) cannot safely perform these operations
    # ============================================
    ENABLE_PROJECT_RAG: bool = os.getenv("ENABLE_PROJECT_RAG", "false").lower() == "true"
    ENABLE_LINK_FETCH: bool = os.getenv("ENABLE_LINK_FETCH", "false").lower() == "true"
    ENABLE_WEB_SCRAPING: bool = os.getenv("ENABLE_WEB_SCRAPING", "false").lower() == "true"
    
    # RAG Configuration
    RAG_CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", 350))  # tokens per chunk
    RAG_CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", 50))
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", 5))  # top chunks to retrieve
    
    # Project Files Storage
    PROJECT_FILES_DIR: str = os.getenv("PROJECT_FILES_DIR", "project_files")
    
    # LM Studio Embedding Endpoint
    LMSTUDIO_EMBEDDING_URL: str = os.getenv("LMSTUDIO_EMBEDDING_URL", "http://localhost:1234/v1/embeddings")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-nomic-embed-text-v1.5")

    # ============================================
    # DATA SOURCE RAG FEATURE FLAGS
    # Uses sentence-transformers (all-MiniLM-L6-v2) for local CPU embedding
    # Works with Mistral 7B for retrieval-augmented generation
    # ============================================
    DATA_SOURCE_RAG_ENABLED: bool = os.getenv("DATA_SOURCE_RAG_ENABLED", "false").lower() == "true"
    
    # Data Source RAG Configuration
    DATA_SOURCE_CHUNK_SIZE: int = int(os.getenv("DATA_SOURCE_CHUNK_SIZE", 1000))  # characters per chunk (800-1200 range)
    DATA_SOURCE_CHUNK_OVERLAP: int = int(os.getenv("DATA_SOURCE_CHUNK_OVERLAP", 100))
    DATA_SOURCE_TOP_K: int = int(os.getenv("DATA_SOURCE_TOP_K", 5))  # top chunks to retrieve
    
    # Data Source Storage
    DATA_SOURCES_DIR: str = os.getenv("DATA_SOURCES_DIR", "data_sources")
    
    # Sentence Transformers Model (runs locally on CPU)
    SENTENCE_TRANSFORMER_MODEL: str = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False
    )


settings = Settings()
