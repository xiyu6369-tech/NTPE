from __future__ import annotations

from typing import Mapping

from .model import TokenUsageEvidence


def _integer(value: object) -> int | None:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return max(0, parsed)


def collect_token_usage(result: Mapping[str, object]) -> TokenUsageEvidence:
    usage = result.get("usage") or result.get("token_usage") or {}
    usage = usage if isinstance(usage, Mapping) else {}
    actual_input = _integer(usage.get("input_tokens", usage.get("prompt_tokens")))
    actual_output = _integer(usage.get("output_tokens", usage.get("completion_tokens")))
    estimated_input = _integer(result.get("estimated_input_tokens")) or 0
    estimated_output = _integer(result.get("estimated_output_tokens")) or 0
    return TokenUsageEvidence(
        estimated_input_tokens=estimated_input,
        estimated_output_tokens=estimated_output,
        actual_input_tokens=actual_input,
        actual_output_tokens=actual_output,
        usage_source="provider" if actual_input is not None or actual_output is not None else "estimate",
    )


def output_tokens(usage: TokenUsageEvidence) -> int:
    return usage.actual_output_tokens if usage.actual_output_tokens is not None else usage.estimated_output_tokens
