
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Mapping, Optional


@dataclass(frozen=True)
class RetryDecision:
    outcome: str
    retry: bool
    stop: bool
    delay_seconds: int
    next_timeout_seconds: int
    next_chunk_size: int
    rebuild_provider_session: bool
    switch_provider: bool
    reason: str
    attempt: int
    max_attempts: int
    metadata: Dict[str, Any]


class AdaptiveRetryPolicy:
    """Pure retry decision engine for translation reliability.

    This module does not execute retries, sleep, call providers, access HTTP,
    read API keys, or modify Translation Runtime. It only returns a decision.
    """

    version = "TE-v4.0"
    stage = "4.0.2"
    name = "adaptive_retry_policy"

    RETRYABLE_OUTCOMES = {
        "http_429",
        "http_500",
        "http_503",
        "read_timeout",
        "connect_timeout",
        "connection_error",
        "ssl_error",
        "json_decode_error",
        "provider_not_attempted",
        "empty_output",
        "too_short",
        "hangul_residue",
        "duplicate_output",
        "retry_exhausted",
        "unknown_failure",
    }

    NON_RETRYABLE_OUTCOMES = {
        "success",
        "invalid_request",
        "authentication_error",
        "forbidden",
        "content_blocked",
    }

    def decide(
        self,
        event: Optional[Mapping[str, Any]] = None,
        policy: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        data = dict(event or {})
        cfg = self._normalize_policy(policy)

        outcome = str(data.get("outcome") or "unknown_failure").strip()
        attempt = max(0, int(data.get("attempt", data.get("retry_count", 0)) or 0))
        max_attempts = max(1, int(data.get("max_attempts", cfg["max_attempts"]) or cfg["max_attempts"]))
        current_timeout = max(1, int(data.get("timeout_seconds", cfg["base_timeout_seconds"]) or cfg["base_timeout_seconds"]))
        current_chunk_size = max(1, int(data.get("chunk_size", cfg["base_chunk_size"]) or cfg["base_chunk_size"]))

        if outcome == "success":
            decision = RetryDecision(
                outcome=outcome,
                retry=False,
                stop=True,
                delay_seconds=0,
                next_timeout_seconds=current_timeout,
                next_chunk_size=current_chunk_size,
                rebuild_provider_session=False,
                switch_provider=False,
                reason="already_successful",
                attempt=attempt,
                max_attempts=max_attempts,
                metadata=self._metadata("success_no_retry"),
            )
            return asdict(decision)

        if outcome in self.NON_RETRYABLE_OUTCOMES:
            decision = RetryDecision(
                outcome=outcome,
                retry=False,
                stop=True,
                delay_seconds=0,
                next_timeout_seconds=current_timeout,
                next_chunk_size=current_chunk_size,
                rebuild_provider_session=False,
                switch_provider=False,
                reason="non_retryable_failure",
                attempt=attempt,
                max_attempts=max_attempts,
                metadata=self._metadata("non_retryable"),
            )
            return asdict(decision)

        if attempt >= max_attempts:
            decision = RetryDecision(
                outcome=outcome,
                retry=False,
                stop=True,
                delay_seconds=0,
                next_timeout_seconds=current_timeout,
                next_chunk_size=current_chunk_size,
                rebuild_provider_session=False,
                switch_provider=bool(cfg["allow_provider_switch"]),
                reason="max_attempts_reached",
                attempt=attempt,
                max_attempts=max_attempts,
                metadata=self._metadata("attempt_limit"),
            )
            return asdict(decision)

        next_attempt = attempt + 1
        delay = self._delay_for(outcome, next_attempt, cfg)
        next_timeout = self._timeout_for(outcome, current_timeout, cfg)
        next_chunk_size = self._chunk_size_for(outcome, current_chunk_size, cfg)
        rebuild = outcome in {
            "provider_not_attempted",
            "connection_error",
            "ssl_error",
            "json_decode_error",
        }

        switch_provider = (
            bool(cfg["allow_provider_switch"])
            and outcome in {"http_503", "http_429", "retry_exhausted"}
            and next_attempt >= int(cfg["provider_switch_after_attempt"])
        )

        decision = RetryDecision(
            outcome=outcome,
            retry=outcome in self.RETRYABLE_OUTCOMES,
            stop=outcome not in self.RETRYABLE_OUTCOMES,
            delay_seconds=delay,
            next_timeout_seconds=next_timeout,
            next_chunk_size=next_chunk_size,
            rebuild_provider_session=rebuild,
            switch_provider=switch_provider,
            reason=self._reason_for(outcome),
            attempt=attempt,
            max_attempts=max_attempts,
            metadata=self._metadata("retry_decision"),
        )
        return asdict(decision)

    def validate_decision(self, decision: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(decision, Mapping):
            return False

        required = {
            "outcome",
            "retry",
            "stop",
            "delay_seconds",
            "next_timeout_seconds",
            "next_chunk_size",
            "rebuild_provider_session",
            "switch_provider",
            "reason",
            "attempt",
            "max_attempts",
            "metadata",
        }
        if not required.issubset(decision):
            return False
        if int(decision.get("delay_seconds", -1)) < 0:
            return False
        if int(decision.get("next_timeout_seconds", 0)) <= 0:
            return False
        if int(decision.get("next_chunk_size", 0)) <= 0:
            return False
        if decision.get("retry") is True and decision.get("stop") is True:
            return False
        if not isinstance(decision.get("metadata"), Mapping):
            return False
        return True

    @staticmethod
    def _normalize_policy(policy: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
        src = dict(policy or {})
        return {
            "max_attempts": max(1, int(src.get("max_attempts", 5) or 5)),
            "base_delay_seconds": max(0, int(src.get("base_delay_seconds", 5) or 5)),
            "max_delay_seconds": max(1, int(src.get("max_delay_seconds", 60) or 60)),
            "base_timeout_seconds": max(1, int(src.get("base_timeout_seconds", 180) or 180)),
            "max_timeout_seconds": max(1, int(src.get("max_timeout_seconds", 300) or 300)),
            "base_chunk_size": max(1, int(src.get("base_chunk_size", 600) or 600)),
            "min_chunk_size": max(1, int(src.get("min_chunk_size", 200) or 200)),
            "provider_switch_after_attempt": max(
                1, int(src.get("provider_switch_after_attempt", 3) or 3)
            ),
            "allow_provider_switch": bool(src.get("allow_provider_switch", False)),
        }

    @staticmethod
    def _delay_for(outcome: str, next_attempt: int, cfg: Mapping[str, Any]) -> int:
        base = int(cfg["base_delay_seconds"])
        cap = int(cfg["max_delay_seconds"])

        if outcome in {"http_429", "http_503"}:
            return min(cap, base * (2 ** max(0, next_attempt - 1)))
        if outcome in {"read_timeout", "connect_timeout"}:
            return min(cap, base * next_attempt)
        if outcome in {"connection_error", "ssl_error"}:
            return min(cap, base * 2)
        if outcome in {"empty_output", "too_short", "hangul_residue", "duplicate_output"}:
            return 0
        if outcome == "provider_not_attempted":
            return 1
        return min(cap, base)

    @staticmethod
    def _timeout_for(outcome: str, current_timeout: int, cfg: Mapping[str, Any]) -> int:
        maximum = int(cfg["max_timeout_seconds"])
        if outcome in {"read_timeout", "connect_timeout"}:
            return min(maximum, max(current_timeout + 30, int(current_timeout * 1.25)))
        return current_timeout

    @staticmethod
    def _chunk_size_for(outcome: str, current_chunk_size: int, cfg: Mapping[str, Any]) -> int:
        minimum = int(cfg["min_chunk_size"])
        if outcome in {"read_timeout", "too_short", "empty_output", "hangul_residue"}:
            return max(minimum, current_chunk_size // 2)
        return current_chunk_size

    @staticmethod
    def _reason_for(outcome: str) -> str:
        reasons = {
            "http_429": "rate_limited_backoff",
            "http_500": "server_error_retry",
            "http_503": "provider_capacity_backoff",
            "read_timeout": "increase_timeout_and_reduce_chunk",
            "connect_timeout": "increase_timeout",
            "connection_error": "rebuild_provider_session",
            "ssl_error": "rebuild_provider_session",
            "json_decode_error": "rebuild_provider_session",
            "provider_not_attempted": "reinitialize_provider_path",
            "empty_output": "retry_with_smaller_chunk",
            "too_short": "retry_with_smaller_chunk",
            "hangul_residue": "retry_with_smaller_chunk",
            "duplicate_output": "retry_translation",
            "retry_exhausted": "consider_provider_switch",
            "unknown_failure": "generic_safe_retry",
        }
        return reasons.get(outcome, "unsupported_outcome")

    def _metadata(self, decision_type: str) -> Dict[str, Any]:
        return {
            "policy": self.name,
            "version": self.version,
            "stage": self.stage,
            "decision_type": decision_type,
            "provider_called": False,
            "http_called": False,
            "api_key_accessed": False,
            "runtime_modified": False,
            "launcher_modified": False,
            "sleep_executed": False,
        }


__all__ = ["RetryDecision", "AdaptiveRetryPolicy"]
