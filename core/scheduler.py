"""
NTPE - Novel Translator Professional Edition
Version : 0.1.0 Alpha
File    : core/scheduler.py
Purpose : RPM limiter for future API calls.
"""

from __future__ import annotations

import time
from collections import deque
from threading import Lock


class RPMScheduler:
    """Simple thread-safe requests-per-minute scheduler."""

    def __init__(self, rpm_limit: int) -> None:
        if rpm_limit <= 0:
            raise ValueError("rpm_limit must be greater than 0")
        self.rpm_limit = rpm_limit
        self._requests: deque[float] = deque()
        self._lock = Lock()

    def wait_turn(self) -> None:
        """Block until a request can be sent without exceeding RPM."""
        with self._lock:
            now = time.time()
            while self._requests and now - self._requests[0] >= 60:
                self._requests.popleft()

            if len(self._requests) >= self.rpm_limit:
                sleep_seconds = 60 - (now - self._requests[0])
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)

            self._requests.append(time.time())

    def current_usage(self) -> int:
        """Return current request count inside the rolling 60-second window."""
        with self._lock:
            now = time.time()
            while self._requests and now - self._requests[0] >= 60:
                self._requests.popleft()
            return len(self._requests)
