from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Tuple

from core.character_memory_v2.models import (
    AddDisposition,
    AddResult,
    ApprovalMetadata,
    ApprovalStatus,
    Evidence,
    EvidenceType,
    FactType,
    MemoryRecord,
    MemoryStatus,
)
from core.character_memory_v2.store import MemoryStore, add_or_merge_memory

from .mapping import SeriesNamespaceMapping, compute_series_character_id, compute_series_fact_id
from .models import (
    SeriesCharacterRecord,
    SeriesFactRecord,
    HydrationReport,
    PromotionRecord,
    AddResult as SeriesAddResult,
    ConflictRecord,
)
from .validation import (
    validate_series_character_record,
    validate_series_fact_record,
    validate_hydration_scope,
    check_hydration_forbidden,
    SeriesMemoryValidationError,
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class SeriesMemoryStore:
    """
    Canonical Series-level character facts store.

    Owns only APPROVED NEVER-expiry facts. Book MemoryStore owns
    local SCENE/CHAPTER/process state.
    """

    def __init__(self, series_id: str) -> None:
        self.series_id = series_id
        self.mapping = SeriesNamespaceMapping()
        self._series_memory_hash: str = ""
        self._promotion_records: list[PromotionRecord] = []

    @property
    def series_memory_hash(self) -> str:
        return self._series_memory_hash

    def _recompute_hash(self) -> str:
        """Recompute the series memory fingerprint."""
        characters = [r.to_dict() for r in self.mapping.get_all_characters()]
        facts = [r.to_dict() for r in self.mapping.get_all_facts()]
        promotions = [r.to_dict() for r in self._promotion_records]
        import json
        payload = {
            "schema_name": "ntpe.series_memory",
            "schema_version": "1.0",
            "series_id": self.series_id,
            "characters": characters,
            "facts": facts,
            "promotions": promotions,
        }
        canonical = json.dumps(
            {k: v for k, v in payload.items() if k != "series_memory_fingerprint"},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def get_canonical_name(self, series_character_id: str) -> Optional[str]:
        """Returns approved canonical name for a character."""
        record = self.mapping.get_character(series_character_id)
        if record and record.fact_type == FactType.CANONICAL_NAME:
            return record.canonical_name
        return None

    def get_relationships(self, series_character_id: str) -> Tuple[SeriesCharacterRecord, ...]:
        """Returns all APPROVED relationships for a character."""
        return tuple(
            r for r in self.mapping.get_all_characters()
            if r.series_character_id == series_character_id
            and r.fact_type == FactType.RELATIONSHIP
        )

    def get_all_canonical_facts(self) -> Tuple[SeriesCharacterRecord, ...]:
        """Returns all SeriesCharacterRecord."""
        return self.mapping.get_all_characters()

    def get_all_canonical_facts_by_type(self, fact_type: FactType) -> Tuple[SeriesCharacterRecord, ...]:
        """Returns facts by FactType."""
        return self.mapping.get_characters_by_fact_type(fact_type)

    def add_or_merge_canonical_fact(
        self,
        record: SeriesCharacterRecord,
        *,
        now: Optional[str] = None,
    ) -> SeriesAddResult:
        """Add or merge a canonical fact into the series store."""
        timestamp = now or utc_now_iso()

        report = validate_series_character_record(record)
        if not report.valid:
            raise SeriesMemoryValidationError(f"Invalid record: {'; '.join(report.errors)}")

        existing = self.mapping.get_character(record.series_character_id)

        if existing is None:
            self.mapping.register_character(self.series_id, record.korean_name, record)
            self._series_memory_hash = self._recompute_hash()
            return SeriesAddResult(
                disposition="accepted",
                record=record,
                message="New canonical fact added",
            )

        if existing.value == record.value:
            return SeriesAddResult(
                disposition="duplicate",
                record=existing,
                message="Canonical fact and value already exist",
            )

        conflict = ConflictRecord(
            conflict_id=hashlib.sha256(
                f"{record.series_character_id}|{record.fact_type.value}|{record.value}|{existing.value}".encode()
            ).hexdigest()[:12],
            series_character_id=record.series_character_id,
            fact_type=record.fact_type,
            record_ids=(existing.series_character_id, record.series_character_id),
            created_at=timestamp,
        )

        return SeriesAddResult(
            disposition="conflict",
            record=record,
            conflict=conflict,
            message="Conflicting canonical value requires MANUAL resolution",
        )

    def hydrate_book_store(
        self,
        book_store: MemoryStore,
        book_identity: str,
        series_memory_hash: str,
    ) -> HydrationReport:
        """
        Copy Series canonical facts into BookMemoryStore as APPROVED records.

        READ-ONLY operation — does not mutate Series state.
        Conservative scope: only allowed fact types are hydrated.
        """
        from .hydration import hydrate_book_store
        return hydrate_book_store(
            series_store=self,
            book_store=book_store,
            book_identity=book_identity,
            series_memory_hash=series_memory_hash,
        )

    def promote_from_book(
        self,
        book_store: MemoryStore,
        book_identity: str,
        approval_gate: bool = True,
    ) -> Tuple[SeriesAddResult, ...]:
        """
        Promote APPROVED facts from BookMemoryStore to SeriesMemoryStore.

        Requires MANUAL approval gate (frozen by D-07).
        Conflict detection: SAME value → NO-OP, DIFFERENT value → CONFLICT.
        """
        from .promotion import promote_from_book
        return promote_from_book(
            series_store=self,
            book_store=book_store,
            book_identity=book_identity,
            approval_gate=approval_gate,
        )

    def validate_integrity(self) -> bool:
        """Verify SHA-256 fingerprint matches stored data."""
        return self._series_memory_hash == self._recompute_hash()


def create_series_character_record(
    *,
    series_id: str,
    korean_name: str,
    canonical_name: str,
    aliases: Tuple[str, ...],
    fact_type: FactType,
    value: str,
    evidence: Tuple[Evidence, ...],
    confidence: float,
    source_books: Tuple[str, ...],
    created_at: Optional[str] = None,
    updated_at: Optional[str] = None,
    version: int = 1,
) -> SeriesCharacterRecord:
    """Factory function to create a SeriesCharacterRecord with proper namespace-isolated ID."""
    timestamp = created_at or utc_now_iso()
    updated = updated_at or timestamp

    series_character_id = compute_series_character_id(series_id, korean_name)

    return SeriesCharacterRecord(
        series_character_id=series_character_id,
        korean_name=korean_name,
        canonical_name=canonical_name,
        aliases=aliases,
        fact_type=fact_type,
        value=value,
        evidence=evidence,
        confidence=confidence,
        approval_status=ApprovalStatus.APPROVED,
        source_books=source_books,
        created_at=timestamp,
        updated_at=updated,
        version=version,
    )