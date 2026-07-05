from __future__ import annotations

import time
from typing import Any, Callable

from .contracts import ProviderError


class RetryPolicy:
    def __init__(self, max_attempts: int = 3, base_delay_seconds: float = 0.0, backoff_factor: float = 2.0):
        self.max_attempts = max_attempts
        self.base_delay_seconds = base_delay_seconds
        self.backoff_factor = backoff_factor

    def run(self, fn: Callable[[], Any]) -> Any:
        last = None
        for attempt in range(self.max_attempts):
            try:
                return fn()
            except ProviderError as exc:
                last = exc
                if not exc.retryable:
                    raise
                if self.base_delay_seconds and attempt < self.max_attempts - 1:
                    time.sleep(self.base_delay_seconds * (self.backoff_factor ** attempt))
        if last:
            raise last
        return fn()

    def to_dict(self):
        return {
            "max_attempts": self.max_attempts,
            "base_delay_seconds": self.base_delay_seconds,
            "backoff_factor": self.backoff_factor,
        }
