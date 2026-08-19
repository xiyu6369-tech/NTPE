"""P0 Stage 5 Batch 5.3 — Series Entity Registry Models.

Persistent Series-level canonical entity mappings.
Namespace-isolated via series_entity_id = sentity_{sha256(series_id|source|type)[:16]}.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Tuple


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class EntityType(str, Enum):
    """Entity types from RM-7.2 (SE-1 frozen)."""
    CHARACTER = "CHARACTER"
    PLACE = "PLACE"
    ORGANIZATION = "ORGANIZATION"
    TERMINOLOGY = "TERMINOLOGY"
    UNKNOWN = "UNKNOWN"


class InjectionSource(str, Enum):
    """Source priority levels (RM-7.2 frozen)."""
    USER = "USER"
    RUNTIME = "RUNTIME"
    LEARNING = "LEARNING"
    AUTO = "AUTO"


class RecordLifecycle(str, Enum):
    """Series entity record lifecycle (SE-5 frozen: per-record versioning)."""
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    ARCHIVED = "ARCHIVED"


class PromotionAction(str, Enum):
    """Promotion action types."""
    CREATED = "created"
    NO_OP = "no_op"
    CONFLICT = "conflict"


@dataclass(frozen=True)
class SeriesEntityRecord:
    """Persistent canonical entity mapping — series-scoped, USER-level authority.

    SE-2 frozen: minimal model — canonical_target only, no EntityNameForms.
    SE-5 frozen: per-record versioning.
    """
    series_entity_id: str           # sentity_{sha256(series_id|source|type)[:16]}
    series_id: str                  # Parent series identity
    source_name: str                # Korean source (e.g., "정태의")
    entity_type: EntityType         # CHARACTER, PLACE, ORGANIZATION, TERMINOLOGY, UNKNOWN
    canonical_target: str           # Approved Chinese (e.g., "鄭泰義")
    version: int                    # Starts at 1, increments on supersede
    lifecycle: RecordLifecycle      # CREATED → ACTIVE → SUPERSEDED → ARCHIVED
    metadata: Dict[str, Any]        # Provenance: source_books, book_coverage, etc.
    approved_at: str                # ISO timestamp of this version
    approved_by: str                # "user" or "series_promotion"
    created_at: str                 # ISO timestamp of initial creation

    def to_dict(self) -> Dict[str, Any]:
        # Handle both EntityType/RecordLifecycle enum and string for entity_type/lifecycle
        et = self.entity_type
        entity_type_value = et.value if hasattr(et, 'value') else et

        lc = self.lifecycle
        lifecycle_value = lc.value if hasattr(lc, 'value') else lc

        return {
            "series_entity_id": self.series_entity_id,
            "series_id": self.series_id,
            "source_name": self.source_name,
            "entity_type": entity_type_value,
            "canonical_target": self.canonical_target,
            "version": self.version,
            "lifecycle": lifecycle_value,
            "metadata": dict(self.metadata),
            "approved_at": self.approved_at,
            "approved_by": self.approved_by,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SeriesEntityRecord":
        return cls(
            series_entity_id=str(data["series_entity_id"]),
            series_id=str(data["series_id"]),
            source_name=str(data["source_name"]),
            entity_type=EntityType(str(data["entity_type"])),
            canonical_target=str(data["canonical_target"]),
            version=int(data["version"]),
            lifecycle=RecordLifecycle(str(data["lifecycle"])),
            metadata=dict(data.get("metadata", {})),
            approved_at=str(data["approved_at"]),
            approved_by=str(data["approved_by"]),
            created_at=str(data["created_at"]),
        )

    def with_superseded_target(
        self,
        new_target: str,
        approved_by: str,
    ) -> "SeriesEntityRecord":
        """Create new version with superseded target (SE-5: per-record versioning)."""
        return SeriesEntityRecord(
            series_entity_id=self.series_entity_id,
            series_id=self.series_id,
            source_name=self.source_name,
            entity_type=self.entity_type,
            canonical_target=new_target,
            version=self.version + 1,
            lifecycle=RecordLifecycle.SUPERSEDED,
            metadata=dict(self.metadata),
            approved_at=utc_now_iso(),
            approved_by=approved_by,
            created_at=self.created_at,
        )

    def with_lifecycle(self, new_lifecycle: RecordLifecycle) -> "SeriesEntityRecord":
        """Create new record with updated lifecycle (e.g., ARCHIVED)."""
        return SeriesEntityRecord(
            series_entity_id=self.series_entity_id,
            series_id=self.series_id,
            source_name=self.source_name,
            entity_type=self.entity_type,
            canonical_target=self.canonical_target,
            version=self.version,
            lifecycle=new_lifecycle,
            metadata=dict(self.metadata),
            approved_at=self.approved_at,
            approved_by=self.approved_by,
            created_at=self.created_at,
        )


@dataclass(frozen=True)
class EntityPromotionRecord:
    """Audit trail for Book → Series entity promotion (D-07: MANUAL only)."""
    promotion_id: str
    series_id: str
    book_identity: str
    source_name: str
    entity_type: EntityType
    previous_target: Optional[str]
    new_target: str
    action: PromotionAction
    resolved_by: Optional[str]        # "user" | None (for conflict)
    resolved_at: str
    source_level: str                 # "USER_OVERRIDE" | "LEARNING"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "promotion_id": self.promotion_id,
            "series_id": self.series_id,
            "book_identity": self.book_identity,
            "source_name": self.source_name,
            "entity_type": self.entity_type.value,
            "previous_target": self.previous_target,
            "new_target": self.new_target,
            "action": self.action.value,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at,
            "source_level": self.source_level,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EntityPromotionRecord":
        return cls(
            promotion_id=str(data["promotion_id"]),
            series_id=str(data["series_id"]),
            book_identity=str(data["book_identity"]),
            source_name=str(data["source_name"]),
            entity_type=EntityType(str(data["entity_type"])),
            previous_target=data.get("previous_target"),
            new_target=str(data["new_target"]),
            action=PromotionAction(str(data["action"])),
            resolved_by=data.get("resolved_by"),
            resolved_at=str(data["resolved_at"]),
            source_level=str(data["source_level"]),
        )


@dataclass(frozen=True)
class ConflictRecord:
    """Record of a conflict between canonical entity values."""
    conflict_id: str
    series_entity_id: str
    entity_type: EntityType
    existing_target: str
    proposed_target: str
    created_at: str
    resolution: Optional[str] = None
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None

    @property
    def unresolved(self) -> bool:
        return self.resolution is None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "series_entity_id": self.series_entity_id,
            "entity_type": self.entity_type.value,
            "existing_target": self.existing_target,
            "proposed_target": self.proposed_target,
            "created_at": self.created_at,
            "resolution": self.resolution,
            "resolved_at": self.resolved_at,
            "resolved_by": self.resolved_by,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ConflictRecord":
        return cls(
            conflict_id=str(data["conflict_id"]),
            series_entity_id=str(data["series_entity_id"]),
            entity_type=EntityType(str(data["entity_type"])),
            existing_target=str(data["existing_target"]),
            proposed_target=str(data["proposed_target"]),
            created_at=str(data["created_at"]),
            resolution=data.get("resolution"),
            resolved_at=data.get("resolved_at"),
            resolved_by=data.get("resolved_by"),
        )


@dataclass(frozen=True)
class AddResult:
    """Result of adding/merging a canonical entity."""
    disposition: str                  # "accepted" | "no_op" | "conflict"
    record: SeriesEntityRecord
    conflict: Optional[ConflictRecord] = None
    message: str = ""


@dataclass(frozen=True)
class HydrationReport:
    """Report of Series → Book hydration operation."""
    series_id: str
    book_identity: str
    hydrated_count: int
    skipped_count: int
    conflict_count: int
    hydration_source: str
    conflicts: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "series_id": self.series_id,
            "book_identity": self.book_identity,
            "hydrated_count": self.hydrated_count,
            "skipped_count": self.skipped_count,
            "conflict_count": self.conflict_count,
            "hydration_source": self.hydration_source,
            "conflicts": list(self.conflicts),
        }


SCHEMA_NAME = "ntpe.series_entity_registry"
SCHEMA_VERSION = "1.0"


def compute_series_entity_id(series_id: str, source_name: str, entity_type: str) -> str:
    """
    Compute namespace-isolated entity ID for Series Entity Registry.

    Canonicalization:
    - source_name: strip whitespace, preserve Unicode
    - entity_type: uppercase (CHARACTER, PLACE, ORGANIZATION, TERMINOLOGY, UNKNOWN)
    """
    canonical_source = source_name.strip()
    canonical_type = entity_type.upper()
    return f"sentity_{hashlib.sha256(f'{series_id}|{canonical_source}|{canonical_type}'.encode()).hexdigest()[:16]}"