"""NTPE 1.0 Beta Stage-01 Production Runtime recovery."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional


@dataclass
class RecoveryResult:
    recovered: bool
    strategy: str = "none"
    attempts: int = 0
    error: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recovered": self.recovered,
            "strategy": self.strategy,
            "attempts": self.attempts,
            "error": self.error,
            "payload": dict(self.payload),
        }


class RuntimeRecoveryManager:
    """Retry and checkpoint-based recovery manager."""

    version = "ntpe-1.0-beta-stage-01"

    def __init__(self, max_retries: int = 2, retry_delay: float = 0.0):
        self.max_retries = max(0, int(max_retries))
        self.retry_delay = max(0.0, float(retry_delay))
        self.last_result = RecoveryResult(recovered=True)

    def run_with_retry(self, func: Callable[[], Any]) -> Any:
        attempts = 0
        last_error: Optional[BaseException] = None
        while attempts <= self.max_retries:
            attempts += 1
            try:
                result = func()
                self.last_result = RecoveryResult(recovered=True, strategy="retry", attempts=attempts)
                return result
            except BaseException as exc:  # noqa: BLE001 - runtime boundary must capture provider failures
                last_error = exc
                if attempts > self.max_retries:
                    break
                if self.retry_delay:
                    time.sleep(self.retry_delay)
        self.last_result = RecoveryResult(recovered=False, strategy="retry", attempts=attempts, error=str(last_error))
        raise last_error  # type: ignore[misc]

    def manifest(self) -> Dict[str, Any]:
        return {"name": "production_runtime_recovery", "version": self.version, "last_result": self.last_result.to_dict()}


__all__ = ["RuntimeRecoveryManager", "RecoveryResult"]
