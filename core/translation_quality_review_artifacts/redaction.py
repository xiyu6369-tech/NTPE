from __future__ import annotations

from collections.abc import Mapping, Sequence

FORBIDDEN_REVIEW_KEYS = frozenset({"api_key", "authorization_id", "execution_token", "provider_request", "prompt", "credential_metadata"})


def assert_review_redacted(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).lower() in FORBIDDEN_REVIEW_KEYS:
                raise ValueError(f"forbidden review field: {key}")
            assert_review_redacted(item)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            assert_review_redacted(item)
