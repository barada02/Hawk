"""Application configuration.

All runtime settings live here and are loaded from environment variables
(and the local .env file in development). Import the shared `settings`
instance everywhere else — never read os.environ directly.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App metadata ---
    APP_NAME: str = "Hawkeye API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # --- Server ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # --- CORS (the Vite frontend runs on 5173 by default) ---
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # --- Gemini ---
    GEMINI_API_KEY: str = ""
    IMAGE_MODEL: str = "gemini-3.1-flash-lite-image"
    VIDEO_MODEL: str = "gemini-omni-flash-preview"
    DEFAULT_ASPECT_RATIO: str = "16:9"

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
