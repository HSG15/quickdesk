from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project Root Directory (where .env lives)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables or .env file.
    Pydantic guarantees type safety and parsing.
    """
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    FRONTEND_URL: str = "http://localhost:5173"

    # PostgreSQL Database URL
    DATABASE_URL: str = "postgresql://localhost:5432/quickdesk"

    # JWT Authentication
    JWT_SECRET_KEY: str = "dev_secret_key_quickdesk_ai_assessment_2026_change_in_prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # AI Configuration (Groq Cloud LLM)
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL_NAME: str = "llama-3.3-70b-versatile"

    # Vector Database & Embeddings
    CHROMA_PERSIST_DIRECTORY: str = "./backend/chroma_db"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    @property
    def sqlalchemy_database_uri(self) -> str:
        """
        Ensure the URI uses the modern psycopg (v3) driver if standard postgresql:// is provided.
        """
        uri = self.DATABASE_URL
        if uri.startswith("postgresql://") and not uri.startswith("postgresql+psycopg://"):
            return uri.replace("postgresql://", "postgresql+psycopg://", 1)
        return uri

    @property
    def cors_origins(self) -> List[str]:
        return [
            self.FRONTEND_URL,
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
        ]

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
