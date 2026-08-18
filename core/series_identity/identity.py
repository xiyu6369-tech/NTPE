from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonicalize_series_key(user_defined_series_key: str) -> str:
    """
    Canonicalize user-provided series key for deterministic ID generation.
    - Strip leading/trailing whitespace
    - Lowercase (ASCII)
    - No other normalization (preserve Unicode as-is)
    """
    return user_defined_series_key.strip().lower()


def compute_series_id(user_defined_series_key: str) -> str:
    """
    Deterministic series identity from user-provided stable series key.

    The series key is canonicalized before hashing.
    """
    canonical_key = canonicalize_series_key(user_defined_series_key)
    return hashlib.sha256(f"series|{canonical_key}".encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class SeriesIdentity:
    """
    Immutable series identity record.

    series_id is immutable after creation.
    series_name is mutable display name.
    """
    series_id: str
    series_name: str
    created_at: str
    updated_at: str

    @classmethod
    def create(cls, user_defined_series_key: str, series_name: str | None = None) -> "SeriesIdentity":
        """Create a new SeriesIdentity from user input."""
        series_id = compute_series_id(user_defined_series_key)
        now = utc_now_iso()
        return cls(
            series_id=series_id,
            series_name=series_name if series_name is not None else user_defined_series_key.strip(),
            created_at=now,
            updated_at=now,
        )

    def with_updated_name(self, new_series_name: str) -> "SeriesIdentity":
        """Return new SeriesIdentity with updated display name (series_id unchanged)."""
        return SeriesIdentity(
            series_id=self.series_id,
            series_name=new_series_name.strip(),
            created_at=self.created_at,
            updated_at=utc_now_iso(),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "series_id": self.series_id,
            "series_name": self.series_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "SeriesIdentity":
        return cls(
            series_id=data["series_id"],
            series_name=data["series_name"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )
