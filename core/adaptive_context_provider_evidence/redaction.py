from __future__ import annotations

from typing import Mapping

FORBIDDEN_FIELDS = {
    "text", "source_text", "translation", "translated_text", "prompt", "system_prompt", "user_prompt",
    "previous_context", "api_key", "authorization", "provider_response", "response_body", "content", "chunks",
}


def assert_redacted(value: object, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).strip().lower()
            if normalized in FORBIDDEN_FIELDS or normalized.endswith("_text"):
                raise ValueError(f"forbidden provider evidence field: {'.'.join((*path, str(key)))}")
            assert_redacted(child, (*path, str(key)))
    elif isinstance(value, (list, tuple)):
        for child in value:
            assert_redacted(child, path)
