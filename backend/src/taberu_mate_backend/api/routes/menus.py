import json
import logging
import mimetypes
from collections.abc import Iterator
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from taberu_mate_backend.api.deps import get_ai_chat_service, get_current_user
from taberu_mate_backend.models.user import User
from taberu_mate_backend.services.ai import (
    AiChatService,
    AiServiceConfigurationError,
    AiServiceRequestError,
)

router = APIRouter(prefix="/menus", tags=["Menus"])
logger = logging.getLogger("uvicorn.error")

_ALLOWED_MENU_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
_MAX_MENU_IMAGE_BYTES = 10 * 1024 * 1024
_STREAM_STATUS_CHAR_INTERVAL = 1_000


@router.post("/scan", response_model=dict[str, Any], summary="Scan menu image")
def scan_menu(
    image: Annotated[UploadFile, File(description="Menu image file")],
    target_language: Annotated[
        str,
        Form(
            min_length=2,
            max_length=40,
            description="Output language code or language name, such as zh-CN, en, ja, or Chinese.",
        ),
    ],
    service: Annotated[AiChatService, Depends(get_ai_chat_service)],
    _current_user: Annotated[User, Depends(get_current_user)],
    model: Annotated[
        str | None,
        Form(min_length=1, max_length=100, description="Optional model override"),
    ] = None,
    prompt: Annotated[
        str | None,
        Form(min_length=1, max_length=4000, description="Optional instruction override"),
    ] = None,
) -> dict[str, Any]:
    media_type = _detect_image_media_type(image)
    logger.info(
        "Menu scan request accepted: filename=%s media_type=%s target_language=%s model=%s",
        image.filename,
        media_type,
        target_language,
        model,
    )
    image_bytes = image.file.read(_MAX_MENU_IMAGE_BYTES + 1)
    if not image_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image is empty")
    if len(image_bytes) > _MAX_MENU_IMAGE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image is too large")
    logger.info(
        "Menu scan image loaded: filename=%s size_bytes=%s",
        image.filename,
        len(image_bytes),
    )

    try:
        logger.info("Menu scan LLM request starting: filename=%s", image.filename)
        return service.scan_menu(
            image_bytes=image_bytes,
            media_type=media_type,
            target_language=target_language,
            model=model,
            prompt=prompt,
        )
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


@router.post("/scan/stream", summary="Scan menu image as a stream")
def stream_menu_scan(
    image: Annotated[UploadFile, File(description="Menu image file")],
    target_language: Annotated[
        str,
        Form(
            min_length=2,
            max_length=40,
            description="Output language code or language name, such as zh-CN, en, ja, or Chinese.",
        ),
    ],
    service: Annotated[AiChatService, Depends(get_ai_chat_service)],
    _current_user: Annotated[User, Depends(get_current_user)],
    model: Annotated[
        str | None,
        Form(min_length=1, max_length=100, description="Optional model override"),
    ] = None,
    prompt: Annotated[
        str | None,
        Form(min_length=1, max_length=4000, description="Optional instruction override"),
    ] = None,
) -> StreamingResponse:
    media_type = _detect_image_media_type(image)
    logger.info(
        "Menu scan stream request accepted: filename=%s media_type=%s target_language=%s model=%s",
        image.filename,
        media_type,
        target_language,
        model,
    )
    image_bytes = image.file.read(_MAX_MENU_IMAGE_BYTES + 1)
    if not image_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image is empty")
    if len(image_bytes) > _MAX_MENU_IMAGE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image is too large")
    logger.info(
        "Menu scan stream image loaded: filename=%s size_bytes=%s",
        image.filename,
        len(image_bytes),
    )

    return StreamingResponse(
        _stream_menu_scan_events(
            service=service,
            image_bytes=image_bytes,
            media_type=media_type,
            target_language=target_language,
            model=model,
            prompt=prompt,
            filename=image.filename or "",
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _detect_image_media_type(image: UploadFile) -> str:
    media_type = _normalize_media_type(image.content_type)
    if media_type is None:
        guessed_media_type, _encoding = mimetypes.guess_type(image.filename or "")
        media_type = _normalize_media_type(guessed_media_type)

    if media_type is None:
        allowed_types = ", ".join(sorted(_ALLOWED_MENU_IMAGE_TYPES))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image type. Allowed types: {allowed_types}",
        )

    return media_type


def _normalize_media_type(media_type: str | None) -> str | None:
    if media_type is None:
        return None

    normalized = media_type.split(";", maxsplit=1)[0].strip().lower()
    if normalized == "image/jpg":
        normalized = "image/jpeg"

    if normalized not in _ALLOWED_MENU_IMAGE_TYPES:
        return None

    return normalized


def _stream_menu_scan_events(
    *,
    service: AiChatService,
    image_bytes: bytes,
    media_type: str,
    target_language: str,
    model: str | None,
    prompt: str | None,
    filename: str,
) -> Iterator[str]:
    content_parts: list[str] = []
    content_char_count = 0
    last_status_char_count = 0
    logger.info("Menu scan stream SSE status sending: filename=%s", filename)
    yield _sse("status", {"message": "图片已上传, 正在识别菜单..."})

    try:
        logger.info("Menu scan stream LLM request starting: filename=%s", filename)
        for delta in service.stream_menu_scan_content(
            image_bytes=image_bytes,
            media_type=media_type,
            target_language=target_language,
            model=model,
            prompt=prompt,
        ):
            content_parts.append(delta)
            content_char_count += len(delta)

            if content_char_count - last_status_char_count >= _STREAM_STATUS_CHAR_INTERVAL:
                last_status_char_count = content_char_count
                logger.info(
                    "Menu scan stream SSE progress sending: filename=%s total_chars=%s",
                    filename,
                    content_char_count,
                )
                yield _sse(
                    "status",
                    {"message": f"正在接收识别结果... {content_char_count} 字符"},
                )

        content = "".join(content_parts)
        if not content.strip():
            msg = "AI provider stream completed without content."
            raise AiServiceRequestError(msg)

        content = _normalize_menu_scan_content(content)

        logger.info("Menu scan stream completed: filename=%s chars=%s", filename, len(content))
        logger.info("Menu scan stream SSE done sending: filename=%s", filename)
        yield _sse("done", {"content": content})
    except (AiServiceConfigurationError, AiServiceRequestError) as exc:
        logger.warning("Menu scan stream failed: filename=%s error=%s", filename, exc)
        logger.info("Menu scan stream SSE error sending: filename=%s", filename)
        yield _sse("error", {"message": str(exc)})


def _sse(event: str, data: dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event}\ndata: {payload}\n\n"


def _normalize_menu_scan_content(content: str) -> str:
    normalized = content.strip()
    if normalized.startswith("```"):
        normalized = normalized.removeprefix("```json").removeprefix("```").strip()
        normalized = normalized.removesuffix("```").strip()

    try:
        parsed = json.loads(normalized)
    except json.JSONDecodeError as exc:
        msg = "模型返回了非 JSON 内容, 请重试。"
        raise AiServiceRequestError(msg) from exc

    if not isinstance(parsed, dict):
        msg = "模型返回的菜单结构不正确, 请重试。"
        raise AiServiceRequestError(msg)

    return json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
