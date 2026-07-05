from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional


class RateLimiter:
    def __init__(self, max_calls: int = 60, window_seconds: float = 60.0):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self.calls: Deque[float] = deque()
        self._provider_calls: Dict[str, Deque[float]] = defaultdict(deque)

    def _allow_queue(self, queue: Deque[float]) -> bool:
        now = time.time()
        while queue and now - queue[0] > self.window_seconds:
            queue.popleft()
        if len(queue) < self.max_calls:
            queue.append(now)
            return True
        return False

    def allow(self, provider: Optional[str] = None) -> bool:
        if provider:
            return self._allow_queue(self._provider_calls[provider])
        return self._allow_queue(self.calls)

    def remaining(self, provider: Optional[str] = None) -> int:
        queue = self._provider_calls[provider] if provider else self.calls
        now = time.time()
        while queue and now - queue[0] > self.window_seconds:
            queue.popleft()
        return max(0, self.max_calls - len(queue))

    def snapshot(self) -> Dict[str, object]:
        return {
            "max_calls": self.max_calls,
            "window_seconds": self.window_seconds,
            "remaining_global": self.remaining(),
            "remaining_by_provider": {name: self.remaining(name) for name in self._provider_calls},
        }
