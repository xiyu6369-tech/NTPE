from __future__ import annotations

from dataclasses import dataclass
import unicodedata


@dataclass(frozen=True)
class ContextBudget:
    available_tokens: int
    reserved_output_tokens: int
    hard_limit: int


def estimate_tokens(text: str) -> int:
    value = str(text or "")
    if not value:
        return 0
    tokens = 0
    latin_run = 0
    digit_run = 0

    def flush_runs() -> None:
        nonlocal tokens, latin_run, digit_run
        tokens += (latin_run + 3) // 4
        tokens += (digit_run + 2) // 3
        latin_run = digit_run = 0

    for char in value:
        code = ord(char)
        if char.isspace():
            flush_runs()
        elif _is_han(code) or _is_hangul(code) or _is_japanese_kana(code):
            flush_runs()
            tokens += 1
        elif char.isascii() and char.isalpha():
            if digit_run:
                flush_runs()
            latin_run += 1
        elif char.isascii() and char.isdigit():
            if latin_run:
                flush_runs()
            digit_run += 1
        else:
            flush_runs()
            if unicodedata.category(char).startswith(("P", "S")):
                tokens += 1
            else:
                tokens += 1
    flush_runs()
    return max(1, tokens)


def _is_han(code: int) -> bool:
    return (0x3400 <= code <= 0x4DBF or 0x4E00 <= code <= 0x9FFF or
            0xF900 <= code <= 0xFAFF or 0x20000 <= code <= 0x323AF)


def _is_hangul(code: int) -> bool:
    return (0xAC00 <= code <= 0xD7A3 or 0x1100 <= code <= 0x11FF or
            0x3130 <= code <= 0x318F or 0xA960 <= code <= 0xA97F or
            0xD7B0 <= code <= 0xD7FF)


def _is_japanese_kana(code: int) -> bool:
    return (0x3040 <= code <= 0x309F or 0x30A0 <= code <= 0x30FF or
            0x31F0 <= code <= 0x31FF or 0xFF66 <= code <= 0xFF9D)


def calculate_dynamic_budget(*, model_context_limit: int, fixed_prompt_tokens: int, source_tokens: int, reserved_output_tokens: int, requested_context_tokens: int | None = None) -> ContextBudget:
    limit = max(0, int(model_context_limit))
    fixed = max(0, int(fixed_prompt_tokens))
    source = max(0, int(source_tokens))
    reserved = max(0, int(reserved_output_tokens))
    hard_limit = max(0, limit - fixed - source - reserved)
    requested = hard_limit if requested_context_tokens is None else max(0, int(requested_context_tokens))
    return ContextBudget(min(hard_limit, requested), reserved, hard_limit)
