"""Hawkeye backend — application entry point.

Keep this file thin: it wires together config, middleware, and routers.
Feature logic lives under app/api/routes/ and app/services/ as we grow.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import generate, health
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
    )

    # CORS — allow the frontend to call the API during development.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Serve locally-stored media (dev only; GCS will replace this).
    media_dir = Path(settings.MEDIA_DIR)
    media_dir.mkdir(parents=True, exist_ok=True)
    app.mount(
        settings.MEDIA_URL_PREFIX,
        StaticFiles(directory=media_dir),
        name="media",
    )

    # Routers. Add new feature routers here as the app grows.
    app.include_router(health.router, prefix="/api")
    app.include_router(generate.router, prefix="/api")

    @app.get("/")
    def root() -> dict:
        return {"message": f"{settings.APP_NAME} is running", "docs": "/docs"}

    return app


app = create_app()
