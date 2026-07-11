"""Hawkeye backend — application entry point.

Keep this file thin: it wires together config, middleware, and routers.
Feature logic lives under app/api/routes/ and app/services/ as we grow.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health
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

    # Routers. Add new feature routers here as the app grows.
    app.include_router(health.router, prefix="/api")

    @app.get("/")
    def root() -> dict:
        return {"message": f"{settings.APP_NAME} is running", "docs": "/docs"}

    return app


app = create_app()
