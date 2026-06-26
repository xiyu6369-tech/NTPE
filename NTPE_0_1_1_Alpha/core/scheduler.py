"""RPM scheduler for API calls.

The scheduler enforces a rolling 60-second request window.
"""

from __future__ import annotations

import time
from collections import deque
from threading import Lock

from core.exceptions import SchedulerError


class RPMScheduler:
    """Rate limiter based on requests per minute."""

    def __init__(self, name: str, rpm_limit: int) -> None:
        if rpm_limit <= 0:
            raise SchedulerError("rpm_limit must be greater than 0")
        self.name = name
        self.rpm_limit = rpm_limit
        self._requests: deque[float] = deque()
        self._lock = Lock()

    def wait_turn(self) -> None:
        """Block until the next request is allowed."""
        with self._lock:
            now = time.time()
            self._drop_expired(now)

            if len(self._requests) >= self.rpm_limit:
                oldest = self._requests[0]
                sleep_seconds = max(60.0 - (now - oldest), 0.0)
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
                now = time.time()
                self._drop_expired(now)

            self._requests.append(time.time())

    def current_usage(self) -> int:
        """Return current request count in the rolling 60-second window."""
        with self._lock:
            now = time.time()
            self._drop_expired(now)
            return len(self._requests)

    def _drop_expired(self, now: float) -> None:
        while self._requests and now - self._requests[0] >= 60.0:
            self._requests.popleft()
