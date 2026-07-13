from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

from .config import BenchmarkConfig

_ACTIVE: ContextVar[BenchmarkConfig | None] = ContextVar("ace_production_benchmark", default=None)


def active_benchmark() -> BenchmarkConfig | None:
    return _ACTIVE.get()


@contextmanager
def benchmark_session(config: BenchmarkConfig) -> Iterator[BenchmarkConfig]:
    token = _ACTIVE.set(config)
    try:
        yield config
    finally:
        _ACTIVE.reset(token)
