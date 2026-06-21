import base64
import json
import logging
import re
from collections.abc import Iterator
from copy import deepcopy
from time import monotonic, time
from typing import Any, Protocol, cast

from openai import OpenAI, OpenAIError

from taberu_mate_backend.core.config import Settings
from taberu_mate_backend.schemas.ai import AiChatRequest, AiJsonSchema
from taberu_mate_backend.schemas.menu_scan import MENU_SCAN_RESPONSE_FORMAT

MENU_SCAN_SYSTEM_PROMPT = """
You are a menu recognition engine for QR-code ordering systems.
Extract all visible menu categories, dishes, prices, options, and useful food metadata from the
image. Translate every translated field into the requested target language. Keep original fields in
the source language found in the image. Use null for unknown nullable fields, empty arrays when no
values are visible, and stable string IDs that can be referenced across categories and items. Return
only data that matches the provided JSON schema. Keep category names, item names, option group
names, and option choice names concise labels. Do not put explanations or repeated phrases into
translated name fields.
""".strip()
logger = logging.getLogger("uvicorn.error")
_STREAM_LOG_CHUNK_INTERVAL = 100
_STREAM_LOG_CHAR_INTERVAL = 1000
_MENU_SCAN_MAX_STREAM_CHARS = 32_000
_STREAM_REPETITION_CHECK_AFTER_CHARS = 12_000
_STREAM_REPETITION_TAIL_CHARS = 1_200
_STREAM_REPETITION_MIN_REPEATS = 6
_STREAM_COMMENTARY_MARKERS = (
    "need valid json",
    "no commentary",
    "let's adjust",
    "i inserted commentary",
    "actually contains",
    "however,",
    "invalid?",
)


class AiServiceConfigurationError(RuntimeError):
    pass


class AiServiceRequestError(RuntimeError):
    pass


class AiChatCompletionsProtocol(Protocol):
    def create(self, **kwargs: Any) -> Any:
        pass


class AiChatProtocol(Protocol):
    @property
    def completions(self) -> AiChatCompletionsProtocol:
        pass


class AiClientProtocol(Protocol):
    @property
    def chat(self) -> AiChatProtocol:
        pass


class AiChatService:
    def __init__(self, settings: Settings, client: AiClientProtocol | None = None) -> None:
        self._settings = settings
        self._client = client

    def ask(self, payload: AiChatRequest) -> dict[str, Any]:
        request_args: dict[str, Any] = {
            "model": payload.model or self._settings.ai_model,
            "messages": self._build_messages(payload),
            "response_format": self._build_response_format(payload),
        }

        if payload.temperature is not None:
            request_args["temperature"] = payload.temperature
        if payload.max_completion_tokens is not None:
            request_args["max_completion_tokens"] = payload.max_completion_tokens

        try:
            completion = self._get_client().chat.completions.create(**request_args)
        except OpenAIError as exc:
            msg = "AI request failed."
            raise AiServiceRequestError(msg) from exc

        return self._validate_completion_response(self._dump_completion(completion))

    def scan_menu(
        self,
        *,
        image_bytes: bytes,
        media_type: str,
        target_language: str,
        model: str | None = None,
        prompt: str | None = None,
    ) -> dict[str, Any]:
        effective_model = model or self._settings.ai_model
        mock_content = self._load_menu_scan_mock_content()
        if mock_content is not None:
            logger.info(
                "AI menu scan mock response used: path=%s chars=%s",
                self._settings.ai_menu_scan_mock_response_path,
                len(mock_content),
            )
            return self._build_mock_chat_completion(mock_content)

        response_schema = _strip_json_schema_annotations(MENU_SCAN_RESPONSE_FORMAT)
        request_args: dict[str, Any] = {
            "model": effective_model,
            "messages": self._build_menu_scan_messages(
                image_bytes=image_bytes,
                media_type=media_type,
                target_language=target_language,
                prompt=prompt,
            ),
            "response_format": {
                "type": "json_schema",
                "json_schema": response_schema,
            },
            "temperature": 0,
        }

        started_at = monotonic()
        logger.info(
            "AI menu scan request prepared: model=%s base_url=%s media_type=%s "
            "image_bytes=%s target_language=%s schema_bytes=%s prompt_chars=%s",
            effective_model,
            self._settings.ai_base_url,
            media_type,
            len(image_bytes),
            target_language,
            _json_size(response_schema),
            len(prompt or MENU_SCAN_SYSTEM_PROMPT),
        )
        try:
            completion = self._get_client().chat.completions.create(**request_args)
            validated = self._validate_completion_response(self._dump_completion(completion))
        except OpenAIError as exc:
            logger.warning(
                "AI menu scan request failed after %.2fs: %s",
                monotonic() - started_at,
                exc,
            )
            msg = "AI menu scan request failed."
            raise AiServiceRequestError(msg) from exc
        except AiServiceRequestError:
            logger.warning(
                "AI menu scan provider returned an invalid/error response after %.2fs",
                monotonic() - started_at,
            )
            raise

        logger.info("AI menu scan request completed in %.2fs", monotonic() - started_at)
        return validated

    def stream_menu_scan_content(
        self,
        *,
        image_bytes: bytes,
        media_type: str,
        target_language: str,
        model: str | None = None,
        prompt: str | None = None,
    ) -> Iterator[str]:
        effective_model = model or self._settings.ai_model
        mock_content = self._load_menu_scan_mock_content()
        if mock_content is not None:
            logger.info(
                "AI menu scan stream mock response used: path=%s chars=%s",
                self._settings.ai_menu_scan_mock_response_path,
                len(mock_content),
            )
            yield from _chunk_text(mock_content)
            return

        response_schema = _strip_json_schema_annotations(MENU_SCAN_RESPONSE_FORMAT)
        request_args: dict[str, Any] = {
            "model": effective_model,
            "messages": self._build_menu_scan_messages(
                image_bytes=image_bytes,
                media_type=media_type,
                target_language=target_language,
                prompt=prompt,
            ),
            "response_format": {
                "type": "json_schema",
                "json_schema": response_schema,
            },
            "temperature": 0,
            "stream": True,
        }

        started_at = monotonic()
        logger.info(
            "AI menu scan stream request prepared: model=%s base_url=%s media_type=%s "
            "image_bytes=%s target_language=%s schema_bytes=%s prompt_chars=%s",
            effective_model,
            self._settings.ai_base_url,
            media_type,
            len(image_bytes),
            target_language,
            _json_size(response_schema),
            len(prompt or MENU_SCAN_SYSTEM_PROMPT),
        )
        try:
            logger.info("AI menu scan stream opening upstream connection")
            stream = self._get_client().chat.completions.create(**request_args)
            logger.info("AI menu scan stream opened after %.2fs", monotonic() - started_at)
            chunk_count = 0
            delta_count = 0
            total_chars = 0
            last_logged_chars = 0
            stream_tail = ""
            for chunk in stream:
                chunk_count += 1
                dumped_chunk = self._dump_completion(chunk)
                self._raise_for_stream_error(dumped_chunk)
                delta_content = _extract_stream_delta_content(dumped_chunk)
                next_total_chars = total_chars + len(delta_content)
                should_log_progress = (
                    chunk_count == 1
                    or chunk_count % _STREAM_LOG_CHUNK_INTERVAL == 0
                    or (
                        delta_content
                        and (
                            delta_count == 0
                            or next_total_chars - last_logged_chars >= _STREAM_LOG_CHAR_INTERVAL
                        )
                    )
                )
                if should_log_progress:
                    logger.info(
                        "AI menu scan stream progress: chunk=%s delta_chars=%s total_chars=%s",
                        chunk_count,
                        len(delta_content),
                        next_total_chars,
                    )
                    last_logged_chars = next_total_chars
                if delta_content:
                    delta_count += 1
                    total_chars = next_total_chars
                    stream_tail = (stream_tail + delta_content)[-_STREAM_REPETITION_TAIL_CHARS:]
                    self._raise_for_unhealthy_stream_output(
                        total_chars=total_chars,
                        stream_tail=stream_tail,
                    )
                    yield delta_content
            logger.info(
                "AI menu scan stream finished: chunks=%s content_chunks=%s "
                "total_chars=%s elapsed=%.2fs",
                chunk_count,
                delta_count,
                total_chars,
                monotonic() - started_at,
            )
        except OpenAIError as exc:
            logger.warning(
                "AI menu scan stream request failed after %.2fs: %s",
                monotonic() - started_at,
                exc,
            )
            msg = "AI menu scan stream request failed."
            raise AiServiceRequestError(msg) from exc
        except AiServiceRequestError:
            logger.warning(
                "AI menu scan stream provider returned an invalid/error response after %.2fs",
                monotonic() - started_at,
            )
            raise

    def _get_client(self) -> AiClientProtocol:
        if self._client is not None:
            return self._client

        if not self._settings.ai_api_key.strip():
            msg = "AI service is not configured. Set TABERU_MATE_AI_API_KEY."
            raise AiServiceConfigurationError(msg)

        client = OpenAI(
            api_key=self._settings.ai_api_key,
            base_url=self._settings.ai_base_url or None,
        )
        logger.info(
            "AI client initialized: base_url=%s model=%s",
            self._settings.ai_base_url,
            self._settings.ai_model,
        )
        self._client = cast(AiClientProtocol, client)
        return self._client

    def _build_messages(self, payload: AiChatRequest) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []

        if payload.prompt is not None and (payload.message is not None or payload.messages):
            messages.append({"role": "system", "content": payload.prompt})
        elif payload.prompt is not None:
            messages.append({"role": "user", "content": payload.prompt})

        messages.extend(
            {"role": message.role, "content": message.content} for message in payload.messages
        )

        if payload.message is not None:
            messages.append({"role": "user", "content": payload.message})

        return messages

    def _build_menu_scan_messages(
        self,
        *,
        image_bytes: bytes,
        media_type: str,
        target_language: str,
        prompt: str | None,
    ) -> list[dict[str, Any]]:
        instruction = prompt or MENU_SCAN_SYSTEM_PROMPT
        encoded_image = base64.b64encode(image_bytes).decode("ascii")
        data_url = f"data:{media_type};base64,{encoded_image}"

        return [
            {"role": "system", "content": instruction},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Recognize this menu image and return structured menu data. "
                            f"Set menu.target_language to {target_language!r} and translate "
                            "all translated fields into that language."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": data_url},
                    },
                ],
            },
        ]

    def _build_response_format(self, payload: AiChatRequest) -> dict[str, Any]:
        if payload.response_format == "json_schema":
            if payload.json_schema is None:
                msg = "json_schema is required when response_format is json_schema."
                raise AiServiceRequestError(msg)
            return {
                "type": "json_schema",
                "json_schema": self._build_json_schema(payload.json_schema),
            }

        return {"type": payload.response_format}

    def _build_json_schema(self, json_schema: AiJsonSchema) -> dict[str, Any]:
        response_schema: dict[str, Any] = {
            "name": json_schema.name,
            "schema": json_schema.schema_,
            "strict": json_schema.strict,
        }
        if json_schema.description is not None:
            response_schema["description"] = json_schema.description
        return response_schema

    def _dump_completion(self, completion: Any) -> dict[str, Any]:
        model_dump = getattr(completion, "model_dump", None)
        if callable(model_dump):
            dumped = model_dump(mode="json")
            if isinstance(dumped, dict):
                return cast(dict[str, Any], dumped)

        if isinstance(completion, dict):
            return cast(dict[str, Any], completion)

        msg = "AI response could not be serialized."
        raise AiServiceRequestError(msg)

    def _validate_completion_response(self, completion: dict[str, Any]) -> dict[str, Any]:
        error = completion.get("error")
        if isinstance(error, dict):
            raise AiServiceRequestError(_format_ai_provider_error(error))

        choices = completion.get("choices")
        if not isinstance(choices, list) or not choices:
            msg = "AI provider response did not include choices."
            raise AiServiceRequestError(msg)

        return completion

    def _raise_for_stream_error(self, chunk: dict[str, Any]) -> None:
        error = chunk.get("error")
        if isinstance(error, dict):
            raise AiServiceRequestError(_format_ai_provider_error(error))

    def _raise_for_unhealthy_stream_output(self, *, total_chars: int, stream_tail: str) -> None:
        if total_chars > _MENU_SCAN_MAX_STREAM_CHARS:
            msg = "模型输出过长, 可能在重复生成, 请重试。"
            raise AiServiceRequestError(msg)

        if (
            total_chars >= _STREAM_REPETITION_CHECK_AFTER_CHARS
            and _has_repeated_tail(stream_tail)
        ):
            msg = "模型输出出现重复生成, 请重试。"
            raise AiServiceRequestError(msg)

        if _has_stream_commentary(stream_tail):
            msg = "模型输出混入了解释内容, 请重试。"
            raise AiServiceRequestError(msg)

    def _load_menu_scan_mock_content(self) -> str | None:
        mock_path = self._settings.ai_menu_scan_mock_response_path
        if mock_path is None:
            return None

        try:
            raw_content = mock_path.expanduser().read_text(encoding="utf-8").strip()
        except OSError as exc:
            msg = f"菜单识别 mock 文件读取失败: {mock_path}"
            raise AiServiceRequestError(msg) from exc

        if not raw_content:
            msg = f"菜单识别 mock 文件为空: {mock_path}"
            raise AiServiceRequestError(msg)

        try:
            parsed = json.loads(raw_content)
        except json.JSONDecodeError as exc:
            msg = f"菜单识别 mock 文件不是合法 JSON: {mock_path}"
            raise AiServiceRequestError(msg) from exc

        content = _extract_chat_completion_content(parsed)
        if content is not None:
            return content

        return json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))

    def _build_mock_chat_completion(self, content: str) -> dict[str, Any]:
        return {
            "id": "chatcmpl_menu_scan_mock",
            "object": "chat.completion",
            "created": int(time()),
            "model": f"mock:{self._settings.ai_menu_scan_mock_response_path}",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            "usage": None,
        }


def _strip_json_schema_annotations(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_json_schema_annotations(deepcopy(nested_value))
            for key, nested_value in value.items()
            if key not in {"$comment", "description"}
        }

    if isinstance(value, list):
        return [_strip_json_schema_annotations(item) for item in value]

    return deepcopy(value)


def _extract_stream_delta_content(chunk: dict[str, Any]) -> str:
    choices = chunk.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""

    content = ""
    for choice in choices:
        if not isinstance(choice, dict):
            continue

        delta = choice.get("delta")
        if not isinstance(delta, dict):
            continue

        delta_content = delta.get("content")
        if isinstance(delta_content, str):
            content += delta_content

    return content


def _extract_chat_completion_content(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None

    choices = value.get("choices")
    if not isinstance(choices, list) or not choices:
        return None

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        return None

    message = first_choice.get("message")
    if not isinstance(message, dict):
        return None

    content = message.get("content")
    if isinstance(content, str):
        return content

    return None


def _format_ai_provider_error(error: dict[str, Any]) -> str:
    message = error.get("message")
    code = error.get("code")
    detail = str(message) if message else "AI provider returned an error response."
    if code:
        return f"{detail} ({code})"
    return detail


def _json_size(value: Any) -> int:
    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def _has_repeated_tail(value: str) -> bool:
    normalized = re.sub(r"\s+", "", value)
    if len(normalized) < 200:
        return False

    max_unit_length = min(80, len(normalized) // _STREAM_REPETITION_MIN_REPEATS)
    for unit_length in range(4, max_unit_length + 1):
        unit = normalized[-unit_length:]
        if len(set(unit)) < 2:
            continue
        if normalized.endswith(unit * _STREAM_REPETITION_MIN_REPEATS):
            return True

    return False


def _has_stream_commentary(value: str) -> bool:
    normalized = re.sub(r"\s+", " ", value).lower()
    return any(marker in normalized for marker in _STREAM_COMMENTARY_MARKERS)


def _chunk_text(value: str, chunk_size: int = 2048) -> Iterator[str]:
    for start in range(0, len(value), chunk_size):
        yield value[start : start + chunk_size]
