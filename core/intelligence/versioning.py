"""Foundation-07.3 Intelligence snapshot versioning utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class SnapshotVersion:
    """Immutable metadata attached to an intelligence snapshot."""

    version_id: str
    revision: int = 1
    created_at: str = field(default_factory=utc_now_iso)
    parent_version_id: Optional[str] = None
    foundation: str = "07.3"

    def bump(self, version_id: Optional[str] = None) -> "SnapshotVersion":
        next_id = version_id or f"{self.version_id}.{self.revision + 1}"
        return SnapshotVersion(
            version_id=next_id,
            revision=self.revision + 1,
            parent_version_id=self.version_id,
            foundation=self.foundation,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_id": self.version_id,
            "revision": self.revision,
            "created_at": self.created_at,
            "parent_version_id": self.parent_version_id,
            "foundation": self.foundation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SnapshotVersion":
        return cls(
            version_id=str(data.get("version_id", "snapshot-1")),
            revision=int(data.get("revision", 1)),
            created_at=str(data.get("created_at") or utc_now_iso()),
            parent_version_id=data.get("parent_version_id"),
            foundation=str(data.get("foundation", "07.3")),
        )
