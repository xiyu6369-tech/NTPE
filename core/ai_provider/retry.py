from __future__ import annotations
from typing import Callable, Any
from .contracts import ProviderError

class RetryPolicy:
    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts
    def run(self, fn: Callable[[], Any]) -> Any:
        last = None
        for _ in range(self.max_attempts):
            try:
                return fn()
            except ProviderError as exc:
                last = exc
                if not exc.retryable:
                    raise
        if last:
            raise last
        return fn()
