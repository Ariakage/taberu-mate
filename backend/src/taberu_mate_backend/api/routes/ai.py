from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from taberu_mate_backend.api.deps import get_ai_chat_service, get_current_user
from taberu_mate_backend.models.user import User
from taberu_mate_backend.schemas.ai import AiChatRequest
from taberu_mate_backend.services.ai import (
    AiChatService,
    AiServiceConfigurationError,
    AiServiceRequestError,
)

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/chat", response_model=dict[str, Any], summary="Ask AI")
def ask_ai(
    payload: AiChatRequest,
    service: Annotated[AiChatService, Depends(get_ai_chat_service)],
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    try:
        return service.ask(payload)
    except AiServiceConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except AiServiceRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
