from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Literal


SpeedProfile = Literal["fast", "balanced", "quality"]


@dataclass(frozen=True)
class RuntimeSpeedPolicy:
    speed: SpeedProfile
    provider_attempts: int
    qa_attempts: int
    timeout_seconds: int
    chunk_size: int
    naturalness_retry: str
    naturalness_retry_limit: int

    def to_dict(self) -> dict:
        return {
            "speed": self.speed,
            "provider_attempts": self.provider_attempts,
            "qa_attempts": self.qa_attempts,
            "timeout_seconds": self.timeout_seconds,
            "chunk_size": self.chunk_size,
            "naturalness_retry": self.naturalness_retry,
            "naturalness_retry_limit": self.naturalness_retry_limit,
        }


_POLICIES: dict[SpeedProfile, RuntimeSpeedPolicy] = {
    "fast": RuntimeSpeedPolicy(
        speed="fast",
        provider_attempts=2,
        qa_attempts=1,
        timeout_seconds=90,
        chunk_size=1200,
        naturalness_retry="off",
        naturalness_retry_limit=0,
    ),
    "balanced": RuntimeSpeedPolicy(
        speed="balanced",
        provider_attempts=2,
        qa_attempts=2,
        timeout_seconds=120,
        chunk_size=1000,
        naturalness_retry="high_confidence_only",
        naturalness_retry_limit=1,
    ),
    "quality": RuntimeSpeedPolicy(
        speed="quality",
        provider_attempts=3,
        qa_attempts=2,
        timeout_seconds=180,
        chunk_size=800,
        naturalness_retry="full",
        naturalness_retry_limit=1,
    ),
}


def normalize_speed(value: str | None) -> SpeedProfile:
    normalized = str(value or "balanced").strip().lower()
    if normalized in _POLICIES:
        return normalized  # type: ignore[return-value]
    return "balanced"


def get_runtime_speed_policy(speed: str | None = None) -> RuntimeSpeedPolicy:
    return _POLICIES[normalize_speed(speed)]


def effective_timeout(policy: RuntimeSpeedPolicy, user_timeout: int | None = None) -> int:
    if user_timeout is None:
        explicit = os.environ.get("NTPE_API_TIMEOUT_EXPLICIT") == "1"
        env_value = os.environ.get("NTPE_API_TIMEOUT")
        if explicit and env_value:
            try:
                user_timeout = max(1, int(float(env_value)))
            except ValueError:
                user_timeout = None
    if user_timeout is None:
        return policy.timeout_seconds

    normalized_timeout = max(1, int(user_timeout))
    # TE v5.2.1: a timeout explicitly supplied by the CLI is authoritative.
    # Speed profiles still provide defaults, but must not silently clamp
    # --api-timeout (for example 180 seconds) back to 90/120 seconds.
    if os.environ.get("NTPE_API_TIMEOUT_EXPLICIT") == "1":
        return normalized_timeout
    return min(policy.timeout_seconds, normalized_timeout)


def naturalness_guard_policy_for_speed(speed: str | None) -> str:
    policy = get_runtime_speed_policy(speed)
    if policy.naturalness_retry == "off":
        return "warn"
    if policy.naturalness_retry == "full":
        return "quality_retry"
    return "high_confidence_only"
