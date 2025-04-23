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
from typing import List, Optional
from pydantic import BaseSettings, Field, root_validator

class Settings(BaseSettings):
    DATA_DIR: Path = Path("data")
    RAG_VECTOR_STORE_PATH: Path = DATA_DIR / "vector_store"
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
    LLM_MODEL_NAME: str = Field(default="mistralai/Mistral-7B-Instruct-v0.3")
    LLM_QUANTIZATION: str = Field(default="none")  # Options: 4bit, 8bit, none
    LLM_MAX_NEW_TOKENS: int = Field(default=32)
    LLM_TIMEOUT_SECONDS: int = Field(default=100)
    LLM_FALLBACK_ENABLED: bool = Field(default=True)
    LLM_FALLBACK_TEXT: str = Field(
        default="I'm sorry, I couldn't process that request in time. Please try again with a simpler query."
    )

    # Hugging Face Inference API
    USE_HF_INFERENCE_API: bool = Field(default=False)
    HF_HUB_TOKEN: Optional[str] = Field(default=None, env="HF_HUB_TOKEN")

    # DeepInfra API settings
    USE_DEEPINFRA_API: bool = Field(default=True)
    DEEPINFRA_API_KEY: Optional[str] = Field(default=None, env="DEEPINFRA_API_KEY")


    # STT settings
    STT_MODEL_SIZE: str = Field(default="base")
    STT_LANGUAGE: Optional[str] = Field(default=None)

    # Live STT settings
    ENABLE_LIVE_STT: bool = Field(default=True)
    LIVE_STT_BUFFER_MS: int = Field(default=500)
    LIVE_STT_SAMPLE_RATE: int = Field(default=16000)
    LIVE_STT_FORMAT: str = Field(default="pcm_s16le")

    # TTS settings
    ENABLE_TTS: bool = Field(default=True)
    TTS_ENGINE: str = Field(default="pyttsx3")
    TTS_VOICE_ID: Optional[str] = Field(default=None)
    TTS_SPEECH_RATE: float = Field(default=1.0)

    # RAG settings
    RAG_ENABLED: bool = Field(default=True)
    RAG_EMBEDDING_MODEL: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    RAG_CHUNK_SIZE: int = Field(default=512)
    RAG_CHUNK_OVERLAP: int = Field(default=50)
    RAG_TOP_K: int = Field(default=5)

    # Banking API settings
    BANKING_API_ENABLED: bool = Field(default=False)
    BANKING_API_URL: Optional[str] = Field(default=None)
    BANKING_API_KEY: Optional[str] = Field(default=None)
    BANKING_API_SECRET: Optional[str] = Field(default=None)
    USE_DUMMY_BANKING_API: bool = Field(default=True)

    # File management
    MAX_UPLOAD_SIZE_MB: int = Field(default=10)
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=[".pdf", ".docx", ".xlsx", ".csv", ".txt"]
    )

    @root_validator
    def create_directories(cls, values):
        data_dir = values.get("DATA_DIR")
        model_dir = values.get("MODEL_DIR")
        vector_store = values.get("RAG_VECTOR_STORE_PATH")
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(model_dir, exist_ok=True)
        os.makedirs(vector_store, exist_ok=True)
        return values

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# instantiate
settings = Settings()

# ensure directories
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.MODEL_DIR, exist_ok=True)
os.makedirs(settings.RAG_VECTOR_STORE_PATH, exist_ok=True)
