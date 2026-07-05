from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol

from core.translation_engine.utils import load_json


RETRYABLE_PROVIDER_ERROR_PATTERNS: tuple[str, ...] = (
    "503",
    "429",
    "resourceexhausted",
    "rate limit",
    "too many requests",
    "service unavailable",
    "timeout",
    "temporarily unavailable",
    "connection reset",
)


class PackageTranslationEngine(Protocol):
    def translate_package(self, package: dict, package_path: str | Path | None = None) -> dict[str, Any]: ...


@dataclass(frozen=True)
class RuntimeProviderPolicy:
    """Stable provider boundary policy for NTPE 1.2 Professional Runtime."""

    max_retries: int = 0
    retry_base_seconds: float = 0.0
    retryable_error_patterns: tuple[str, ...] = RETRYABLE_PROVIDER_ERROR_PATTERNS

    def attempts(self) -> int:
        return max(1, int(self.max_retries) + 1)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["retryable_error_patterns"] = list(self.retryable_error_patterns)
        return payload


@dataclass
class RuntimeProviderTrace:
    attempts: list[dict[str, Any]] = field(default_factory=list)

    def add(self, *, attempt: int, status: str, error: str = "") -> None:
        record = {"attempt": attempt, "status": status}
        if error:
            record["error"] = error
        self.attempts.append(record)

    @property
    def total_attempts(self) -> int:
        return len(self.attempts)

    def to_dict(self) -> dict[str, Any]:
        return {"total_attempts": self.total_attempts, "attempts": list(self.attempts)}


def is_retryable_provider_error(error: str, patterns: tuple[str, ...] = RETRYABLE_PROVIDER_ERROR_PATTERNS) -> bool:
    lowered = str(error or "").lower()
    return any(pattern.lower() in lowered for pattern in patterns)


def provider_retry_delay_seconds(attempt: int, base_seconds: float) -> float:
    return max(0.0, float(base_seconds)) * (2 ** max(0, int(attempt) - 1))


class RuntimeProviderAdapter:
    """Adapter that makes TranslationEngine provider calls observable and replaceable.

    Stage-03 keeps TranslationEngine intact, but all package calls made by
    TranslationRuntime now pass through this adapter. TXT and batch LTS entrypoints
    remain callable as before and can adopt this boundary incrementally later.
    """

    def __init__(self, engine: PackageTranslationEngine, policy: RuntimeProviderPolicy | None = None) -> None:
        self.engine = engine
        self.policy = policy or RuntimeProviderPolicy()

    def translate_package_file(self, package_path: str | Path) -> dict[str, Any]:
        package_path = Path(package_path)
        if not package_path.exists():
            return {"status": "failed", "error": f"Prompt Package 不存在：{package_path}", "provider_trace": RuntimeProviderTrace().to_dict()}
        package = load_json(package_path)
        return self.translate_package(package, package_path=package_path)

    def translate_package(self, package: dict, package_path: str | Path | None = None) -> dict[str, Any]:
        trace = RuntimeProviderTrace()
        last_result: dict[str, Any] = {"status": "failed", "error": "provider call was not attempted"}
        for attempt in range(1, self.policy.attempts() + 1):
            result = self.engine.translate_package(package, package_path=package_path)
            if not isinstance(result, dict):
                result = {"status": "failed", "error": "provider returned non-dict result"}
            result = dict(result)
            result["provider_attempt"] = attempt
            status = str(result.get("status", ""))
            error = str(result.get("error", ""))
            trace.add(attempt=attempt, status=status or "unknown", error=error)
            result["provider_trace"] = trace.to_dict()
            last_result = result
            if status == "success":
                return result
            if attempt >= self.policy.attempts() or not is_retryable_provider_error(error, self.policy.retryable_error_patterns):
                return result
            delay = provider_retry_delay_seconds(attempt, self.policy.retry_base_seconds)
            if delay > 0:
                time.sleep(delay)
        return last_result
