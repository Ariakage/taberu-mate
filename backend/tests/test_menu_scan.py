from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient

from taberu_mate_backend.api.deps import get_ai_chat_service, get_current_user
from taberu_mate_backend.core.config import Settings
from taberu_mate_backend.main import create_app
from taberu_mate_backend.models.user import User
from taberu_mate_backend.services.ai import (
    AiChatService,
    AiServiceRequestError,
    _has_repeated_tail,
    _has_stream_commentary,
)


class FakeCompletions:
    def __init__(self) -> None:
        self.last_kwargs: dict[str, Any] | None = None

    def create(self, **kwargs: Any) -> dict[str, Any]:
        self.last_kwargs = kwargs
        return {
            "id": "chatcmpl_menu_test",
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "{\"menu\":{\"target_language\":\"en\"}}",
                    },
                    "finish_reason": "stop",
                }
            ],
        }


class FakeChat:
    def __init__(self, completions: FakeCompletions) -> None:
        self.completions = completions


class FakeClient:
    def __init__(self) -> None:
        self.completions = FakeCompletions()
        self.chat = FakeChat(self.completions)


class StubAiChatService:
    def __init__(self) -> None:
        self.call: dict[str, Any] | None = None

    def scan_menu(
        self,
        *,
        image_bytes: bytes,
        media_type: str,
        target_language: str,
        model: str | None,
        prompt: str | None,
    ) -> dict[str, Any]:
        self.call = {
            "image_bytes": image_bytes,
            "media_type": media_type,
            "target_language": target_language,
            "model": model,
            "prompt": prompt,
        }
        return {
            "id": "chatcmpl_menu_route_test",
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "{\"items\":[]}"},
                    "finish_reason": "stop",
                }
            ],
        }


def test_menu_scan_service_sends_image_and_schema(tmp_path: Path) -> None:
    settings = Settings(
        database_path=tmp_path / "test.db",
        auth_token_secret="test-auth-token-secret-with-enough-length",
        ai_api_key="test-key",
        ai_model="test-vision-model",
        ai_menu_scan_mock_response_path=None,
    )
    fake_client = FakeClient()
    service = AiChatService(settings=settings, client=fake_client)

    response = service.scan_menu(
        image_bytes=b"fake-image",
        media_type="image/png",
        target_language="en",
    )

    assert response["object"] == "chat.completion"
    assert fake_client.completions.last_kwargs is not None
    kwargs = fake_client.completions.last_kwargs
    assert kwargs["model"] == "test-vision-model"
    assert kwargs["temperature"] == 0
    assert kwargs["response_format"]["type"] == "json_schema"
    assert kwargs["response_format"]["json_schema"]["name"] == "scan_order_menu"
    assert kwargs["response_format"]["json_schema"]["strict"] is True
    user_content = kwargs["messages"][1]["content"]
    assert user_content[0]["type"] == "text"
    assert "en" in user_content[0]["text"]
    assert user_content[1]["type"] == "image_url"
    assert user_content[1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_menu_scan_service_rejects_error_body(tmp_path: Path) -> None:
    settings = Settings(
        database_path=tmp_path / "test.db",
        auth_token_secret="test-auth-token-secret-with-enough-length",
        ai_api_key="test-key",
        ai_model="test-vision-model",
        ai_menu_scan_mock_response_path=None,
    )
    fake_client = FakeClient()
    service = AiChatService(settings=settings, client=fake_client)

    def create_error_response(**_kwargs: Any) -> dict[str, Any]:
        return {
            "id": None,
            "choices": None,
            "error": {
                "message": "stream error: stream ID 1; INTERNAL_ERROR",
                "code": "internal_server_error",
            },
        }

    fake_client.completions.create = create_error_response

    try:
        service.scan_menu(
            image_bytes=b"fake-image",
            media_type="image/png",
            target_language="en",
        )
    except AiServiceRequestError as exc:
        assert "stream error" in str(exc)
        assert "internal_server_error" in str(exc)
    else:
        raise AssertionError("Expected AiServiceRequestError")


def test_menu_scan_detects_repeated_stream_tail() -> None:
    assert _has_repeated_tail("套餐/单点。" * 40)


def test_menu_scan_allows_normal_stream_tail() -> None:
    normal_tail = (
        '{"categories":[{"id":"cat_lunch","name_translated":"午餐"}],'
        '"items":[{"id":"item_gyoza","name_translated":"饺子"}]}'
    )

    assert not _has_repeated_tail(normal_tail)


def test_menu_scan_detects_stream_commentary() -> None:
    assert _has_stream_commentary(
        'However need valid JSON no commentary. Let\'s adjust final already invalid?'
    )


def test_menu_scan_service_uses_mock_response_file(tmp_path: Path) -> None:
    mock_path = tmp_path / "mock-menu.json"
    mock_path.write_text(
        '{"menu":{"target_language":"zh-CN"},"categories":[],"items":[]}',
        encoding="utf-8",
    )
    settings = Settings(
        database_path=tmp_path / "test.db",
        auth_token_secret="test-auth-token-secret-with-enough-length",
        ai_api_key="",
        ai_model="test-vision-model",
        ai_menu_scan_mock_response_path=mock_path,
    )
    service = AiChatService(settings=settings)

    response = service.scan_menu(
        image_bytes=b"fake-image",
        media_type="image/png",
        target_language="zh-CN",
    )

    assert response["id"] == "chatcmpl_menu_scan_mock"
    assert response["choices"][0]["message"]["content"] == (
        '{"menu":{"target_language":"zh-CN"},"categories":[],"items":[]}'
    )


def test_menu_scan_stream_uses_mock_response_file(tmp_path: Path) -> None:
    mock_path = tmp_path / "mock-menu.json"
    mock_path.write_text(
        '{"menu":{"target_language":"zh-CN"},"categories":[],"items":[]}',
        encoding="utf-8",
    )
    settings = Settings(
        database_path=tmp_path / "test.db",
        auth_token_secret="test-auth-token-secret-with-enough-length",
        ai_api_key="",
        ai_model="test-vision-model",
        ai_menu_scan_mock_response_path=mock_path,
    )
    service = AiChatService(settings=settings)

    content = "".join(
        service.stream_menu_scan_content(
            image_bytes=b"fake-image",
            media_type="image/png",
            target_language="zh-CN",
        )
    )

    assert content == '{"menu":{"target_language":"zh-CN"},"categories":[],"items":[]}'


def test_menu_scan_requires_authenticated_user(tmp_path: Path) -> None:
    settings = Settings(
        database_path=tmp_path / "test.db",
        auth_token_secret="test-auth-token-secret-with-enough-length",
    )
    app = create_app(settings)
    client = TestClient(app)

    response = client.post(
        "/api/v1/menus/scan",
        data={"target_language": "en"},
        files={"image": ("menu.png", b"fake-image", "image/png")},
    )

    assert response.status_code == 401


def test_menu_scan_route_passes_file_to_service(tmp_path: Path) -> None:
    settings = Settings(
        database_path=tmp_path / "test.db",
        auth_token_secret="test-auth-token-secret-with-enough-length",
    )
    app = create_app(settings)
    stub_service = StubAiChatService()
    app.dependency_overrides[get_ai_chat_service] = lambda: stub_service
    app.dependency_overrides[get_current_user] = _authenticated_user
    client = TestClient(app)

    response = client.post(
        "/api/v1/menus/scan",
        data={"target_language": "zh-CN", "model": "vision-test-model"},
        files={"image": ("menu.jpg", b"fake-image", "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.json()["object"] == "chat.completion"
    assert stub_service.call == {
        "image_bytes": b"fake-image",
        "media_type": "image/jpeg",
        "target_language": "zh-CN",
        "model": "vision-test-model",
        "prompt": None,
    }


def _authenticated_user() -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid4(),
        username="menuuser",
        nickname="Menu User",
        avatar_url=None,
        password_salt="salt",
        password_hash="hash",
        created_at=now,
        updated_at=now,
    )
