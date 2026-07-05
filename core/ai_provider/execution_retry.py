from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from .retry import RetryPolicy


@dataclass
class ExecutionRetryState:
    attempts: int = 0
    retries: int = 0
    failures: int = 0
    retryable_failures: int = 0
    last_error: str | None = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "attempts": self.attempts,
            "retries": self.retries,
            "failures": self.failures,
            "retryable_failures": self.retryable_failures,
            "last_error": self.last_error,
        }


@dataclass
class ExecutionRetryPolicy:
    policy: RetryPolicy = field(default_factory=RetryPolicy)

    @property
    def max_attempts(self) -> int:
        return self.policy.max_attempts

    def to_dict(self) -> Dict[str, object]:
        return self.policy.to_dict()
