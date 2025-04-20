import os
from pathlib import Path
from typing import List, Optional

from pydantic import BaseSettings, Field, root_validator


class Settings(BaseSettings):
    # Base directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = Field(default=BASE_DIR / "data")
    MODEL_DIR: Path = Field(default=BASE_DIR / "models")
    RAG_VECTOR_STORE_PATH: Path = Field(default=DATA_DIR / "vector_store")

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
    LLM_QUANTIZATION: str = Field(default="none")
    LLM_MAX_NEW_TOKENS: int = Field(default=512)
    LLM_TIMEOUT_SECONDS: int = Field(default=30)
    LLM_FALLBACK_ENABLED: bool = Field(default=True)
    LLM_FALLBACK_TEXT: str = Field(
        default="I'm sorry, I couldn't process that request in time. Please try again with a simpler query."
    )

    # STT settings
    STT_MODEL_SIZE: str = Field(default="base")
    STT_LANGUAGE: Optional[str] = Field(default=None)

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

    # File management settings
    MAX_UPLOAD_SIZE_MB: int = Field(default=10)
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=[".pdf", ".docx", ".xlsx", ".csv", ".txt"]
    )

    @root_validator(pre=True)
    def create_dirs_and_set_cache(cls, values):
        """Ensure directories exist and configure HF cache env vars."""
        base = Path(values.get("BASE_DIR", cls.BASE_DIR))
        data_dir = Path(values.get("DATA_DIR", base / "data"))
        model_dir = Path(values.get("MODEL_DIR", base / "models"))
        vector_store = Path(values.get("RAG_VECTOR_STORE_PATH", data_dir / "vector_store"))

        for d in (data_dir, model_dir, vector_store):
            d.mkdir(parents=True, exist_ok=True)

        # Direct HF cache into model_dir
        os.environ.setdefault("TRANSFORMERS_CACHE", str(model_dir))
        os.environ.setdefault("HF_HOME", str(model_dir))

        return values

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Instantiate to apply directory creation and env setup
settings = Settings()
