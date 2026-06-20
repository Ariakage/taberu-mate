from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from taberu_mate_backend.api.router import api_router
from taberu_mate_backend.core.config import Settings, get_settings
from taberu_mate_backend.core.errors import configure_error_handlers
from taberu_mate_backend.db.session import init_db


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    init_db(settings)

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        debug=settings.debug,
    )

    def get_app_settings() -> Settings:
        return settings

    app.dependency_overrides[get_settings] = get_app_settings
    configure_error_handlers(app, settings)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {
            "message": f"Welcome to {settings.app_name}",
            "docs": "/docs",
            "health": f"{settings.api_v1_prefix}/health",
        }

    return app


app = create_app()
