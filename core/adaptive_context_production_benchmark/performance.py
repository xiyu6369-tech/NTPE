from __future__ import annotations

from typing import Any, Iterable

from .model import BenchmarkRun, ChunkEvidence


def _sum(rows: Iterable[ChunkEvidence], name: str) -> float:
    return sum(float(getattr(row, name) or 0) for row in rows)


def compare_performance(baseline: BenchmarkRun, candidate: BenchmarkRun, paired: tuple[tuple[ChunkEvidence, ChunkEvidence], ...]) -> dict[str, Any]:
    b_rows = tuple(left for left, _ in paired)
    c_rows = tuple(right for _, right in paired)
    b_calls = int(_sum(b_rows, "provider_calls")); c_calls = int(_sum(c_rows, "provider_calls"))
    b_attempts = int(_sum(b_rows, "provider_attempts")); c_attempts = int(_sum(c_rows, "provider_attempts"))
    b_latency = round(_sum(b_rows, "provider_latency_ms"), 3); c_latency = round(_sum(c_rows, "provider_latency_ms"), 3)
    delta_latency = round(c_latency - b_latency, 3)
    b_prompt = int(_sum(b_rows, "prompt_tokens")); c_prompt = int(_sum(c_rows, "prompt_tokens"))
    b_context = int(_sum(b_rows, "context_tokens")); c_context = int(_sum(c_rows, "context_tokens"))
    sampled = sum(row.ace_state in {"activated", "sampled_fallback"} for row in candidate.chunks)
    return {
        "baseline_provider_calls": b_calls, "candidate_provider_calls": c_calls, "provider_calls_delta": c_calls - b_calls,
        "provider_calls_added": max(0, c_calls - b_calls),
        "baseline_provider_attempts": b_attempts, "candidate_provider_attempts": c_attempts, "provider_attempts_delta": c_attempts - b_attempts,
        "baseline_latency_total_ms": b_latency, "candidate_latency_total_ms": c_latency, "latency_delta_ms": delta_latency,
        "latency_reduction_ratio": round((b_latency - c_latency) / b_latency, 6) if b_latency else 0.0,
        "baseline_timeout_count": int(_sum(b_rows, "timeout_count")), "candidate_timeout_count": int(_sum(c_rows, "timeout_count")),
        "baseline_503_count": int(_sum(b_rows, "http_503_count")), "candidate_503_count": int(_sum(c_rows, "http_503_count")),
        "baseline_execution_total_ms": baseline.execution_total_ms, "candidate_execution_total_ms": candidate.execution_total_ms,
        "baseline_prompt_tokens": b_prompt, "candidate_prompt_tokens": c_prompt, "prompt_tokens_saved": b_prompt - c_prompt,
        "baseline_context_tokens": b_context, "candidate_context_tokens": c_context, "context_tokens_saved": b_context - c_context,
        "activated_chunks": sum(row.ace_state == "activated" for row in c_rows),
        "fallback_chunks": sum(row.ace_state == "sampled_fallback" for row in candidate.chunks),
        "sampled_chunks": sampled, "paired_chunks": len(paired),
        "performance_gain": (b_prompt > c_prompt) or (b_context > c_context) or (b_latency > c_latency),
        "provider_latency_source": "request_timing",
    }
