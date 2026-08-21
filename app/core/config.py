"""
Application Settings module powered by pydantic-settings.
"""

from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # STT Settings
    STT_PROVIDER: Literal["sarvam", "elevenlabs"] = "sarvam"
    SARVAM_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""

    # Generation Settings
    LLM_PROVIDER: str = "groq"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "llama-3.1-8b-instant"

    # Retrieval Settings
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    VECTOR_DB_TYPE: Literal["faiss", "qdrant", "memory"] = "faiss"

    # Latency Target
    MAX_LATENCY_SLA_MS: float = 200.0


settings = Settings()
