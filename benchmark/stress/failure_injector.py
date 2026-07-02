from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Set


class InjectedFailure(RuntimeError):
    pass


@dataclass
class FailureInjector:
    """Deterministic failure injection for benchmark-only workloads."""

    fail_at: Set[int] = field(default_factory=set)
    failure_type: str = "provider_timeout"
    injected: int = 0
    recovered: int = 0

    def should_fail(self, index: int) -> bool:
        return index in self.fail_at

    def execute(self, index: int, fn: Callable[[], Any], recovery: Callable[[Exception], Any] | None = None) -> Any:
        try:
            if self.should_fail(index):
                self.injected += 1
                raise InjectedFailure(self.failure_type)
            return fn()
        except Exception as exc:
            if recovery is None:
                raise
            self.recovered += 1
            return recovery(exc)

    def metrics(self) -> Dict[str, Any]:
        return {
            "failure_type": self.failure_type,
            "injected_failures": self.injected,
            "recovered_failures": self.recovered,
        }


def build_failure_injector(fail_every: int | None = None, count: int = 0, failure_type: str = "provider_timeout") -> FailureInjector:
    fail_at: Set[int] = set()
    if fail_every and fail_every > 0:
        fail_at = {index for index in range(count) if index > 0 and index % fail_every == 0}
    return FailureInjector(fail_at=fail_at, failure_type=failure_type)
