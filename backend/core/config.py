"""Application configuration loaded from environment variables."""

import os
from pathlib import Path
from dataclasses import dataclass, field

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
REPORTS_DIR = PROJECT_ROOT / "reports"
DATASETS_DIR = PROJECT_ROOT / "datasets"


@dataclass
class Settings:
    """Application settings with defaults for local development."""

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{PROJECT_ROOT / 'trademark_screening.db'}"
    )

    # API
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    api_cors_origins: list[str] = field(default_factory=lambda: os.getenv(
        "API_CORS_ORIGINS", "http://localhost:5173"
    ).split(","))

    # Gemini API
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

    # Similarity weights
    weight_phonetic: float = float(os.getenv("WEIGHT_PHONETIC", "0.35"))
    weight_textual: float = float(os.getenv("WEIGHT_TEXTUAL", "0.30"))
    weight_goods: float = float(os.getenv("WEIGHT_GOODS", "0.35"))

    # Priority thresholds
    threshold_high: float = float(os.getenv("THRESHOLD_HIGH", "75"))
    threshold_medium: float = float(os.getenv("THRESHOLD_MEDIUM", "50"))
    threshold_low: float = float(os.getenv("THRESHOLD_LOW", "25"))

    # Auth
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )

    # Embedding model
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def has_gemini(self) -> bool:
        return bool(self.gemini_api_key)


settings = Settings()
