from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient

from taberu_mate_backend.api.deps import get_ai_chat_service, get_current_user
from taberu_mate_backend.core.config import Settings
from taberu_mate_backend.main import create_app
from taberu_mate_backend.models.user import User
from taberu_mate_backend.schemas.ai import AiChatRequest
from taberu_mate_backend.services.ai import AiChatService, AiServiceRequestError


class FakeCompletion:
    def model_dump(self, *, mode: str) -> dict[str, Any]:
        assert mode == "json"
        return {
            "id": "chatcmpl_test",
            "object": "chat.completion",
            "created": 1_800_000_000,
            "model": "test-model",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "{\"title\":\"Dinner\"}"},
                    "finish_reason": "stop",
                }
            ],
        }


class FakeCompletions:
    def __init__(self) -> None:
        self.last_kwargs: dict[str, Any] | None = None

    def create(self, **kwargs: Any) -> FakeCompletion:
        self.last_kwargs = kwargs
        return FakeCompletion()


class FakeChat:
    def __init__(self, completions: FakeCompletions) -> None:
        self.completions = completions


class FakeClient:
    def __init__(self) -> None:
        self.completions = FakeCompletions()
        self.chat = FakeChat(self.completions)


class StubAiChatService:
    def __init__(self) -> None:
        self.payload: AiChatRequest | None = None

    def ask(self, payload: AiChatRequest) -> dict[str, Any]:
        self.payload = payload
        return {
            "id": "chatcmpl_route_test",
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "hello"},
                    "finish_reason": "stop",
                }
            ],
        }


def test_ai_service_calls_chat_completions_with_json_schema(tmp_path: Path) -> None:
    settings = Settings(
        database_path=tmp_path / "test.db",
        auth_token_secret="test-auth-token-secret-with-enough-length",
        ai_api_key="test-key",
        ai_model="test-model",
    )
    fake_client = FakeClient()
    service = AiChatService(settings=settings, client=fake_client)

    response = service.ask(
        AiChatRequest(
            prompt="Return a dinner menu.",
            message="Build tonight's dinner.",
            json_schema={
                "name": "dinner_menu",
                "schema": {
                    "type": "object",
                    "properties": {"title": {"type": "string"}},
                    "required": ["title"],
                    "additionalProperties": False,
                },
            },
        )
    )

    assert response["object"] == "chat.completion"
    assert fake_client.completions.last_kwargs == {
        "model": "test-model",
        "messages": [
            {"role": "system", "content": "Return a dinner menu."},
            {"role": "user", "content": "Build tonight's dinner."},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "dinner_menu",
                "schema": {
                    "type": "object",
                    "properties": {"title": {"type": "string"}},
                    "required": ["title"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        },
    }


def test_ai_route_returns_chat_completion_response(tmp_path: Path) -> None:
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
        "/api/v1/ai/chat",
        json={"message": "Say hello.", "response_format": "json_object"},
    )

    assert response.status_code == 200
    assert response.json()["object"] == "chat.completion"
    assert stub_service.payload is not None
    assert stub_service.payload.message == "Say hello."
    assert stub_service.payload.response_format == "json_object"


def test_ai_route_requires_authenticated_user(tmp_path: Path) -> None:
    settings = Settings(
        database_path=tmp_path / "test.db",
        auth_token_secret="test-auth-token-secret-with-enough-length",
    )
    app = create_app(settings)
    client = TestClient(app)

    response = client.post("/api/v1/ai/chat", json={"message": "Say hello."})

    assert response.status_code == 401


def test_ai_service_rejects_error_body(tmp_path: Path) -> None:
    settings = Settings(
        database_path=tmp_path / "test.db",
        auth_token_secret="test-auth-token-secret-with-enough-length",
        ai_api_key="test-key",
        ai_model="test-model",
    )
    fake_client = FakeClient()
    service = AiChatService(settings=settings, client=fake_client)

    def create_error_response(**_kwargs: Any) -> dict[str, Any]:
        return {
            "id": None,
            "choices": None,
            "error": {"message": "bad response status code 504", "code": "server_error"},
        }

    fake_client.completions.create = create_error_response

    try:
        service.ask(AiChatRequest(message="hello"))
    except AiServiceRequestError as exc:
        assert "bad response status code 504" in str(exc)
        assert "server_error" in str(exc)
    else:
        raise AssertionError("Expected AiServiceRequestError")


def _authenticated_user() -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid4(),
        username="aiuser",
        nickname="AI User",
        avatar_url=None,
        password_salt="salt",
        password_hash="hash",
        created_at=now,
        updated_at=now,
    )
