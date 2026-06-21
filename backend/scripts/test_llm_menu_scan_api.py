from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

from openai import OpenAI, OpenAIError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"
DEFAULT_SCHEMA_SOURCE = PROJECT_ROOT / "src/taberu_mate_backend/schemas/menu_scan.py"
DEFAULT_IMAGE_PATH = Path.home() / "Downloads/114514.jpg"

MENU_SCAN_SYSTEM_PROMPT = """
You are a menu recognition engine for QR-code ordering systems.
Extract all visible menu categories, dishes, prices, options, and useful food metadata from the
image. Translate every translated field into the requested target language. Keep original fields in
the source language found in the image. Use null for unknown nullable fields, empty arrays when no
values are visible, and stable string IDs that can be referenced across categories and items. Return
only data that matches the provided JSON schema.
""".strip()


def main() -> int:
    args = parse_args()
    load_env_file(args.env)

    api_key = args.api_key or os.environ.get("TABERU_MATE_AI_API_KEY") or os.environ.get(
        "OPENAI_API_KEY"
    )
    base_url = args.base_url or os.environ.get("TABERU_MATE_AI_BASE_URL")
    model = args.model or os.environ.get("TABERU_MATE_AI_MODEL") or "gpt-5.5"

    if not api_key:
        print(
            "Missing API key. Set TABERU_MATE_AI_API_KEY in .env or pass --api-key.",
            file=sys.stderr,
        )
        return 2

    image_path = args.image.expanduser().resolve()
    if not image_path.exists():
        print(f"Image not found: {image_path}", file=sys.stderr)
        return 2

    response_schema = build_response_schema(args.schema)
    media_type = detect_media_type(image_path)
    image_bytes = image_path.read_bytes()
    messages = build_messages(
        image_bytes=image_bytes,
        media_type=media_type,
        target_language=args.target_language,
        prompt=args.prompt,
    )

    request_args: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "response_format": {
            "type": "json_schema",
            "json_schema": response_schema,
        },
    }
    if args.stream:
        request_args["stream"] = True
    if args.temperature is not None:
        request_args["temperature"] = args.temperature
    if args.max_completion_tokens is not None:
        request_args["max_completion_tokens"] = args.max_completion_tokens

    print("=== request ===")
    print(f"base_url: {base_url or 'default OpenAI SDK base URL'}")
    print(f"model: {model}")
    print(f"stream: {args.stream}")
    print(f"schema: {args.schema} ({json_size(response_schema)} bytes)")
    print(f"image: {image_path} ({len(image_bytes)} bytes, {media_type})")
    print(f"target_language: {args.target_language}")
    print()

    client = OpenAI(api_key=api_key, base_url=base_url or None, timeout=args.timeout)
    started_at = perf_counter()

    try:
        if args.stream:
            content = run_stream_request(client, request_args)
        else:
            content = run_non_stream_request(client, request_args)
    except OpenAIError as exc:
        print(f"\nOpenAI SDK error after {perf_counter() - started_at:.2f}s:")
        print(exc)
        return 1
    except RuntimeError as exc:
        print(f"\nProvider error after {perf_counter() - started_at:.2f}s:")
        print(exc)
        return 1

    elapsed = perf_counter() - started_at
    print()
    print(f"=== completed in {elapsed:.2f}s ===")
    print(f"content chars: {len(content)}")
    print()
    print("=== raw content ===")
    print(content)
    print()
    print_parsed_summary(content)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Directly test the OpenAI-compatible menu scan chat.completions API."
    )
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE_PATH)
    parser.add_argument("--env", type=Path, default=DEFAULT_ENV_PATH)
    parser.add_argument("--api-key")
    parser.add_argument("--base-url")
    parser.add_argument("--model")
    parser.add_argument("--target-language", default="zh-CN")
    parser.add_argument("--schema", choices=["menu", "simple"], default="menu")
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--max-completion-tokens", type=int)
    parser.add_argument("--timeout", type=float, default=240.0)
    parser.add_argument("--prompt")
    return parser.parse_args()


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", maxsplit=1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


def build_response_schema(schema_mode: str) -> dict[str, Any]:
    if schema_mode == "simple":
        return {
            "name": "menu_probe",
            "strict": True,
            "schema": {
                "type": "object",
                "required": ["restaurant_name", "items"],
                "additionalProperties": False,
                "properties": {
                    "restaurant_name": {"type": "string"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name", "price"],
                            "additionalProperties": False,
                            "properties": {
                                "name": {"type": "string"},
                                "price": {"type": "string"},
                            },
                        },
                    },
                },
            },
        }

    return load_menu_schema_from_backend()


def load_menu_schema_from_backend() -> dict[str, Any]:
    source = DEFAULT_SCHEMA_SOURCE.read_text(encoding="utf-8")
    match = re.search(r'json\.loads\(\s*("""|\'\'\')(?P<body>.*?)(\1)\s*\)', source, re.S)
    if match is None:
        raise RuntimeError(f"Could not extract menu schema JSON from {DEFAULT_SCHEMA_SOURCE}")

    return strip_schema_annotations(json.loads(match.group("body")))


def strip_schema_annotations(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: strip_schema_annotations(nested_value)
            for key, nested_value in value.items()
            if key not in {"$comment", "description"}
        }
    if isinstance(value, list):
        return [strip_schema_annotations(item) for item in value]
    return value


def detect_media_type(path: Path) -> str:
    media_type, _encoding = mimetypes.guess_type(path.name)
    if media_type == "image/jpg":
        return "image/jpeg"
    if media_type in {"image/jpeg", "image/png", "image/webp"}:
        return media_type
    return "image/jpeg"


def build_messages(
    *,
    image_bytes: bytes,
    media_type: str,
    target_language: str,
    prompt: str | None,
) -> list[dict[str, Any]]:
    data_url = f"data:{media_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"
    return [
        {"role": "system", "content": prompt or MENU_SCAN_SYSTEM_PROMPT},
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
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        },
    ]


def run_non_stream_request(client: OpenAI, request_args: dict[str, Any]) -> str:
    print("Sending non-stream request...")
    completion = client.chat.completions.create(**request_args)
    dumped = completion.model_dump(mode="json")
    error = dumped.get("error")
    if isinstance(error, dict):
        raise RuntimeError(f"Provider returned error body: {error}")

    print(f"id: {dumped.get('id')}")
    print(f"object: {dumped.get('object')}")
    print(f"model: {dumped.get('model')}")
    print(f"usage: {dumped.get('usage')}")
    content = dumped["choices"][0]["message"].get("content")
    return content or ""


def run_stream_request(client: OpenAI, request_args: dict[str, Any]) -> str:
    print("Opening stream request...")
    stream = client.chat.completions.create(**request_args)
    parts: list[str] = []
    started_at = perf_counter()

    for index, chunk in enumerate(stream, start=1):
        dumped = chunk.model_dump(mode="json")
        error = dumped.get("error")
        if isinstance(error, dict):
            raise RuntimeError(f"Provider returned stream error body: {error}")

        delta = extract_delta_content(dumped)
        if delta:
            parts.append(delta)
            print(
                f"[chunk {index}] +{len(delta)} chars, total={sum(len(part) for part in parts)}"
            )
        else:
            print(f"[chunk {index}] no text delta")

    print(f"Stream closed after {perf_counter() - started_at:.2f}s.")
    return "".join(parts)


def extract_delta_content(chunk: dict[str, Any]) -> str:
    choices = chunk.get("choices")
    if not isinstance(choices, list):
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


def print_parsed_summary(content: str) -> None:
    print("=== parsed summary ===")
    try:
        parsed = json.loads(strip_markdown_fence(content))
    except json.JSONDecodeError as exc:
        print(f"Could not parse content as JSON: {exc}")
        return

    if isinstance(parsed, dict):
        print(f"top-level keys: {', '.join(parsed.keys())}")
        categories = parsed.get("categories")
        items = parsed.get("items")
        if isinstance(categories, list):
            print(f"categories: {len(categories)}")
        if isinstance(items, list):
            print(f"items: {len(items)}")
    else:
        print(f"parsed JSON type: {type(parsed).__name__}")


def strip_markdown_fence(content: str) -> str:
    stripped = content.strip()
    stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.I)
    stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def json_size(value: Any) -> int:
    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
