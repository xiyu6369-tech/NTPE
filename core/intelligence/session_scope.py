"""Foundation-07.3 Intelligence session scope definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .versioning import utc_now_iso


@dataclass
class IntelligenceSessionScope:
    """Describes where intelligence memory belongs during a runtime flow."""

    job_id: str = "default-job"
    runtime_id: str = "default-runtime"
    session_id: str = "default-session"
    segment_id: Optional[str] = None
    created_at: str = field(default_factory=utc_now_iso)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def child_for_segment(self, segment_id: str, metadata: Optional[Dict[str, Any]] = None) -> "IntelligenceSessionScope":
        next_metadata = dict(self.metadata)
        next_metadata.update(dict(metadata or {}))
        return IntelligenceSessionScope(
            job_id=self.job_id,
            runtime_id=self.runtime_id,
            session_id=self.session_id,
            segment_id=segment_id,
            metadata=next_metadata,
        )

    def key(self) -> str:
        parts = [self.job_id, self.runtime_id, self.session_id]
        if self.segment_id:
            parts.append(self.segment_id)
        return ":".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "runtime_id": self.runtime_id,
            "session_id": self.session_id,
            "segment_id": self.segment_id,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
            "scope_key": self.key(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntelligenceSessionScope":
        return cls(
            job_id=str(data.get("job_id", "default-job")),
            runtime_id=str(data.get("runtime_id", "default-runtime")),
            session_id=str(data.get("session_id", "default-session")),
            segment_id=data.get("segment_id"),
            created_at=str(data.get("created_at") or utc_now_iso()),
            metadata=dict(data.get("metadata", {})),
        )
