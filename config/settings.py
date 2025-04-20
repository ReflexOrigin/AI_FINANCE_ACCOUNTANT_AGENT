"""
Finance Accountant Agent Configuration Settings

This module contains all configuration settings for the Finance Accountant Agent.
Settings are loaded from environment variables with sensible defaults.

Configuration categories:
- Server settings (host, port, debug mode)
- Security settings (secret keys, allowed origins)
- LLM settings (model path, quantization level)
- Speech-to-Text settings (Whisper model size)
- Text-to-Speech settings (engine selection)
- RAG settings (embedding model, vector store path)
- Banking API credentials
- Logging configuration
"""

import os
from pathlib import Path
from typing import List, Optional, Union

from pydantic import BaseSettings, Field, root_validator

class Settings(BaseSettings):
    DATA_DIR: Path = Path("data")
    RAG_VECTOR_STORE_PATH: Path = DATA_DIR / "vector_store"
    # Base paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    MODEL_DIR: Path = Field(default=BASE_DIR / "models")

    # Server settings
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    DEBUG_MODE: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")

    # Security settings
    SECRET_KEY: str = Field(default="")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    ALLOWED_ORIGINS: List[str] = Field(default=["*"])
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_MAX_REQUESTS: int = Field(default=100)
    RATE_LIMIT_TIMEFRAME_SECONDS: int = Field(default=3600)

    # LLM settings
    LLM_MODEL_NAME: str = Field(default="microsoft/phi-4")
    LLM_QUANTIZATION: str = Field(default="None")  # Options: 4bit, 8bit, none
    LLM_MAX_NEW_TOKENS: int = Field(default=512)
    LLM_TIMEOUT_SECONDS: int = Field(default=30)
    LLM_FALLBACK_ENABLED: bool = Field(default=True)
    LLM_FALLBACK_TEXT: str = Field(
        default="I'm sorry, I couldn't process that request in time. Please try again with a simpler query."
    )

    # STT settings
    STT_MODEL_SIZE: str = Field(default="base")  # Options: tiny, base, small, medium, large
    STT_LANGUAGE: Optional[str] = Field(default=None)  # None for auto-detection

    # TTS settings
    ENABLE_TTS: bool = Field(default=True)
    TTS_ENGINE: str = Field(default="pyttsx3")  # Options: mozilla, pyttsx3
    TTS_VOICE_ID: Optional[str] = Field(default=None)
    TTS_SPEECH_RATE: float = Field(default=1.0)

    # RAG settings
    RAG_ENABLED: bool = Field(default=True)
    RAG_EMBEDDING_MODEL: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    RAG_VECTOR_STORE_PATH: Path = Field(default=DATA_DIR / "vector_store")
    RAG_CHUNK_SIZE: int = Field(default=512)
    RAG_CHUNK_OVERLAP: int = Field(default=50)
    RAG_TOP_K: int = Field(default=5)

    # Banking API settings
    BANKING_API_ENABLED: bool = Field(default=False)
    BANKING_API_URL: Optional[str] = Field(default=None)
    BANKING_API_KEY: Optional[str] = Field(default=None)
    BANKING_API_SECRET: Optional[str] = Field(default=None)
    USE_DUMMY_BANKING_API: bool = Field(default=True)

    # File management settings
    MAX_UPLOAD_SIZE_MB: int = Field(default=10)
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=[".pdf", ".docx", ".xlsx", ".csv", ".txt"]
    )

    @root_validator
    def create_directories(cls, values):
        """Ensure required directories exist."""
        data_dir = values.get("DATA_DIR")
        model_dir = values.get("MODEL_DIR")
        vector_store_path = values.get("RAG_VECTOR_STORE_PATH")

        if data_dir:
            os.makedirs(data_dir, exist_ok=True)
        if model_dir:
            os.makedirs(model_dir, exist_ok=True)
        if vector_store_path:
            os.makedirs(vector_store_path, exist_ok=True)

        return values

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Ensure directories exist
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.MODEL_DIR, exist_ok=True)
os.makedirs(settings.RAG_VECTOR_STORE_PATH, exist_ok=True)
