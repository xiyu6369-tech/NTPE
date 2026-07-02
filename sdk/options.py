"""Stage-07.2 SDK Translation options.

Additive public options object for SDK Translation API. This module does not
modify frozen Foundation, CLI, SDK Core, or SDK Session contracts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class TranslationOptions:
    """Stable options for SDK translation calls."""

    source_language: str = "ko"
    target_language: str = "zh-TW"
    job_id: str = "sdk-translation-job"
    model: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    async_mode: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_language": self.source_language,
            "target_language": self.target_language,
            "job_id": self.job_id,
            "model": self.model,
            "metadata": dict(self.metadata),
            "async_mode": self.async_mode,
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]] = None) -> "TranslationOptions":
        payload = dict(data or {})
        return cls(
            source_language=str(payload.get("source_language", "ko")),
            target_language=str(payload.get("target_language", "zh-TW")),
            job_id=str(payload.get("job_id", "sdk-translation-job")),
            model=payload.get("model"),
            metadata=dict(payload.get("metadata", {}) or {}),
            async_mode=bool(payload.get("async_mode", False)),
        )
