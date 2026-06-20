from functools import lru_cache
from pathlib import Path
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_AUTH_TOKEN_SECRET = "dev-auth-token-secret-change-me-before-deploy"
_DEPLOY_ENVIRONMENTS = {"production", "prod", "staging"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="TABERU_MATE_",
        extra="ignore",
    )

    app_name: str = "TaberuMate API"
    version: str = "0.1.0"
    environment: str = "local"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    database_path: Path = Path("data/taberu_mate.db")
    auth_token_secret: str = Field(default=_DEV_AUTH_TOKEN_SECRET, min_length=32)
    access_token_expire_minutes: int = Field(default=15, gt=0)
    refresh_token_expire_days: int = Field(default=30, gt=0)
    access_token_cookie_name: str = "access_token"
    refresh_token_cookie_name: str = "refresh_token"
    csrf_cookie_name: str = "csrf_token"
    csrf_header_name: str = "X-CSRF-Token"
    auth_cookie_secure: bool = True
    auth_cookie_samesite: str = "strict"
    auth_login_rate_limit: int = Field(default=5, gt=0)
    auth_login_rate_limit_window_seconds: int = Field(default=300, gt=0)
    sentry_dsn: str | None = None
    allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
    )

    @model_validator(mode="after")
    def reject_development_secrets_for_deployments(self) -> Self:
        if (
            self.environment.lower() in _DEPLOY_ENVIRONMENTS
            and self.auth_token_secret == _DEV_AUTH_TOKEN_SECRET
        ):
            msg = "Production-like environments must set a real token secret."
            raise ValueError(msg)

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
