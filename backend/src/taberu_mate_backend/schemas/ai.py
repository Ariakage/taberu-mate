from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

AiChatRole = Literal["developer", "system", "user", "assistant"]
AiResponseFormat = Literal["text", "json_object", "json_schema"]


class AiChatMessage(BaseModel):
    role: AiChatRole
    content: str = Field(min_length=1)


class AiJsonSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    schema_: dict[str, Any] = Field(alias="schema")
    description: str | None = Field(default=None, min_length=1)
    strict: bool = True


class AiChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str | None = Field(default=None, min_length=1)
    message: str | None = Field(default=None, min_length=1)
    messages: list[AiChatMessage] = Field(default_factory=list, max_length=50)
    response_format: AiResponseFormat = "text"
    json_schema: AiJsonSchema | None = None
    model: str | None = Field(default=None, min_length=1)
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_completion_tokens: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_chat_request(self) -> Self:
        if self.prompt is None and self.message is None and not self.messages:
            msg = "Either prompt, message, or messages must be provided."
            raise ValueError(msg)

        if self.json_schema is not None:
            self.response_format = "json_schema"

        if self.response_format == "json_schema" and self.json_schema is None:
            msg = "json_schema is required when response_format is json_schema."
            raise ValueError(msg)

        return self
