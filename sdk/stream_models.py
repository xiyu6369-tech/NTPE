"""Stage-07.4 SDK Streaming models."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .options import TranslationOptions


@dataclass
class StreamOptions:
    """Stable options for SDK streaming translation calls."""

    source_language: str = "ko"
    target_language: str = "zh-TW"
    job_id: str = "sdk-stream-job"
    model: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    emit_tokens: bool = True
    emit_segments: bool = True
    continue_on_error: bool = False

    def to_translation_options(self, *, segment_index: int = 0) -> TranslationOptions:
        metadata = dict(self.metadata)
        metadata.setdefault("sdk_stream_segment_index", segment_index)
        return TranslationOptions(
            source_language=self.source_language,
            target_language=self.target_language,
            job_id=self.job_id,
            model=self.model,
            metadata=metadata,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_language": self.source_language,
            "target_language": self.target_language,
            "job_id": self.job_id,
            "model": self.model,
            "metadata": dict(self.metadata),
            "emit_tokens": self.emit_tokens,
            "emit_segments": self.emit_segments,
            "continue_on_error": self.continue_on_error,
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]] = None) -> "StreamOptions":
        payload = dict(data or {})
        return cls(
            source_language=str(payload.get("source_language", "ko")),
            target_language=str(payload.get("target_language", "zh-TW")),
            job_id=str(payload.get("job_id", "sdk-stream-job")),
            model=payload.get("model"),
            metadata=dict(payload.get("metadata", {}) or {}),
            emit_tokens=bool(payload.get("emit_tokens", True)),
            emit_segments=bool(payload.get("emit_segments", True)),
            continue_on_error=bool(payload.get("continue_on_error", False)),
        )


@dataclass
class StreamState:
    """Serializable progress state for a streaming session."""

    status: str = "created"
    total_segments: int = 0
    completed_segments: int = 0
    event_count: int = 0
    current_segment_index: Optional[int] = None

    @property
    def progress(self) -> float:
        if self.total_segments <= 0:
            return 100.0 if self.status == "completed" else 0.0
        return round((self.completed_segments / self.total_segments) * 100.0, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "total_segments": self.total_segments,
            "completed_segments": self.completed_segments,
            "event_count": self.event_count,
            "current_segment_index": self.current_segment_index,
            "progress": self.progress,
        }
