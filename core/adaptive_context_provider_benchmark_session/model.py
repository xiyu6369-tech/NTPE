from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

SESSION_VERSION = "7.0.0-stage10.2"


@dataclass(frozen=True)
class ProviderAttemptPlan:
    attempt: int
    model: str
    timeout_seconds: int
    fallback_used: bool = False
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0

    def __post_init__(self) -> None:
        if self.attempt < 1 or not self.model or self.timeout_seconds < 1:
            raise ValueError("invalid caller-owned Provider attempt plan")


@dataclass(frozen=True)
class SessionSummary:
    pair_id: str
    run_kind: str
    state: str
    attempts_planned: int
    attempts_executed: int
    successful_attempts: int
    failed_attempts: int
    timeout_attempts: int
    http_503_attempts: int
    total_latency_ms: float
    payload_preserved: bool
    prompt_preserved: bool
    provider_failure_decoupled: bool = True
    readiness_evaluated: bool = False
    content_redacted: bool = True
    version: str = SESSION_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
