from typing import Annotated

from fastapi import APIRouter, Depends

from taberu_mate_backend.core.config import Settings, get_settings
from taberu_mate_backend.schemas.health import HealthCheck

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthCheck, summary="Health check")
def health_check(settings: Annotated[Settings, Depends(get_settings)]) -> HealthCheck:
    return HealthCheck(
        status="ok",
        service=settings.app_name,
        environment=settings.environment,
        version=settings.version,
    )
