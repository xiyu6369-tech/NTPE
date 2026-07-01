from __future__ import annotations
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_calls: int = 60, window_seconds: float = 60.0):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self.calls = deque()
    def allow(self) -> bool:
        now = time.time()
        while self.calls and now - self.calls[0] > self.window_seconds:
            self.calls.popleft()
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        return False
    def remaining(self) -> int:
        return max(0, self.max_calls - len(self.calls))
