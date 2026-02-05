import os
import base64
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ValidationError

class Settings(BaseSettings):
    """
    Application settings with Production Safeguards.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Security / Encryption ─────────────────────────────────────────────────────
    VIGIL_ENC_KEY: str = ""
    ENCRYPTION_KEY: bytes = b""

    # ── API Keys ──────────────────────────────────────────────────────────────────
    VIBHISHAN_API_KEY: str = "gov_secure_access_2026"
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # ── Deployment Config ─────────────────────────────────────────────────────────
    ENVIRONMENT: str = "development"  # 'production' or 'development'
    BASE_URL: str = "http://localhost:8000"

    # ── Government / External Endpoints ───────────────────────────────────────────
    AADHAAR_API: str = ""
    CYBER_CRIME_PORTAL: str = ""

    MOCK_SCAMMER_API_URL: str = ""
    MOCK_SCAMMER_API_KEY: str = ""
    MOCK_SCAMMER_TIMEOUT_SECONDS: float = 2.0

    EVAL_SCHEMA: str = "judge"

    # ── Application Metadata ──────────────────────────────────────────────────────
    PROJECT_NAME: str = "VIBHISHAN: National Cyber Defense"
    VERSION: str = "2.1.0 (Patch 1)"
    TRAINING_MODE: bool = False # Set to True during train_brain.py run

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        raw_key = self.VIGIL_ENC_KEY
        if not raw_key:
            raw_key = base64.urlsafe_b64encode(os.urandom(32)).decode()
        self.ENCRYPTION_KEY = base64.urlsafe_b64encode(raw_key.encode()[:32])
        self._validate_production_config()

    def _validate_production_config(self):
        """Hard fail if configured incorrectly for production."""
        if self.ENVIRONMENT.lower() == "production":
            if "localhost" in self.BASE_URL or "127.0.0.1" in self.BASE_URL:
                raise ValueError(
                    "CRITICAL CONFIG ERROR: You are in PRODUCTION mode but BASE_URL is set to localhost. "
                    "Judges/Bots will not be able to access generated images/audio. "
                    "Set BASE_URL to your Render/Public URL."
                )

SETTINGS = Settings()