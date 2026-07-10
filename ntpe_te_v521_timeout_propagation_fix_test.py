from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from core.translation_runtime.runtime_speed_policy import effective_timeout, get_runtime_speed_policy
from lts.txt_translation_runtime import (
    TxtTranslationOptions,
    _effective_provider_timeout,
    apply_runtime_speed_policy,
)


@contextmanager
def temporary_env(**updates: str | None):
    previous = {name: os.environ.get(name) for name in updates}
    try:
        for name, value in updates.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def _package(speed_timeout: int | None, source_chars: int = 575) -> dict:
    runtime: dict[str, int] = {}
    if speed_timeout is not None:
        runtime["speed_timeout"] = speed_timeout
    return {"source": {"char_count": source_chars}, "runtime": runtime}


def test_explicit_cli_timeout_is_not_clamped_by_speed_policy() -> None:
    balanced = get_runtime_speed_policy("balanced")
    with temporary_env(NTPE_API_TIMEOUT="180", NTPE_API_TIMEOUT_EXPLICIT="1"):
        assert effective_timeout(balanced) == 180
        options = apply_runtime_speed_policy(
            TxtTranslationOptions(
                input_path=Path("sample.txt"),
                output_dir=Path("output"),
                speed="balanced",
            )
        )
        assert options.user_api_timeout == 180
        assert options.runtime_timeout == 180


def test_explicit_cli_timeout_reaches_provider_attempts() -> None:
    with temporary_env(NTPE_API_TIMEOUT="180", NTPE_API_TIMEOUT_EXPLICIT="1"):
        assert _effective_provider_timeout(_package(120), 1) == 180
        assert _effective_provider_timeout(_package(120), 2) == 180


def test_non_explicit_speed_policy_behavior_is_unchanged() -> None:
    balanced = get_runtime_speed_policy("balanced")
    fast = get_runtime_speed_policy("fast")
    with temporary_env(NTPE_API_TIMEOUT="180", NTPE_API_TIMEOUT_EXPLICIT=None):
        assert effective_timeout(balanced) == 120
        assert effective_timeout(fast, user_timeout=180) == 90
        assert _effective_provider_timeout(_package(120), 1) == 120


def test_legacy_short_chunk_defaults_remain_compatible() -> None:
    with temporary_env(
        NTPE_API_TIMEOUT="180",
        NTPE_API_TIMEOUT_EXPLICIT=None,
        NTPE_SHORT_CHUNK_FIRST_TIMEOUT="90",
        NTPE_RETRY_TIMEOUT="120",
    ):
        assert _effective_provider_timeout(_package(None), 1) == 90
        assert _effective_provider_timeout(_package(None), 2) == 120


def main() -> int:
    tests = (
        ("Explicit CLI timeout bypasses speed clamp", test_explicit_cli_timeout_is_not_clamped_by_speed_policy),
        ("Explicit timeout reaches provider attempts", test_explicit_cli_timeout_reaches_provider_attempts),
        ("Non-explicit behavior remains compatible", test_non_explicit_speed_policy_behavior_is_unchanged),
        ("Legacy short-chunk defaults remain compatible", test_legacy_short_chunk_defaults_remain_compatible),
    )
    print("NTPE TE v5.2.1 Regression Timeout Propagation Fix")
    print("==================================================")
    for label, test in tests:
        test()
        print(f"{label:<47} PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
