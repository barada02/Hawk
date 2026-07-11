"""Application configuration.

All runtime settings live here and are loaded from environment variables
(and the local .env file in development). Import the shared `settings`
instance everywhere else — never read os.environ directly.
"""

from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    # --- App metadata ---
    APP_NAME: str = "Hawkeye API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # --- Server ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # --- CORS ---
    # Comma-separated list of allowed origins. Set CORS_ORIGINS in the
    # environment on the deployed service, e.g.
    #   CORS_ORIGINS=https://hawkeye-web-xxxx.run.app,https://app.example.com
    # Defaults to the local Vite dev server.
    CORS_ORIGINS: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors_origins(cls, value: object) -> object:
        # Accept a plain comma-separated string from the env var.
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    # --- Gemini ---
    GEMINI_API_KEY: str = ""
    IMAGE_MODEL: str = "gemini-3.1-flash-lite-image"
    VIDEO_MODEL: str = "models/gemini-omni-flash-preview"
    DEFAULT_ASPECT_RATIO: str = "16:9"

    # Video generation params (drive quality/consistency of Omni output).
    VIDEO_DURATION: str = "10s"
    VIDEO_THINKING_LEVEL: str = "high"
    VIDEO_MAX_OUTPUT_TOKENS: int = 65536
    # Resolution the reference image is fed at (low|medium|high|ultra_high).
    # Higher = the clip stays truer to the keyframe.
    VIDEO_IMAGE_RESOLUTION: str = "high"

    # --- Media storage ---
    # Local for now; swap to a GCS-backed Storage later (bucket created out-of-band).
    MEDIA_DIR: str = "media"
    MEDIA_URL_PREFIX: str = "/media"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (parsed once per process)."""
    return Settings()


settings = get_settings()
