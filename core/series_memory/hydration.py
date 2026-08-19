from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Tuple

from core.character_memory_v2.models import (
    AddDisposition,
    ApprovalMetadata,
    ApprovalStatus,
    Evidence,
    EvidenceType,
    ExpiryKind,
    ExpiryPolicy,
    FactType,
    MemoryRecord,
    MemoryStatus,
)
from core.character_memory_v2.store import MemoryStore, add_or_merge_memory

from .models import HydrationReport
from .store import SeriesMemoryStore
from .validation import (
    ALLOWED_HYDRATION_FACT_TYPES,
    check_hydration_forbidden,
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def create_hydration_evidence(
    series_id: str,
    series_memory_hash: str,
    source_record: Any,
    book_source_case_id: str = "series_hydration",
    book_source_segment_id: str = "hydration",
) -> Evidence:
    """Create evidence for a hydrated record."""
    return Evidence(
        evidence_id=f"series_hydration_{hashlib.sha256(f'{series_id}|{source_record.series_character_id}'.encode()).hexdigest()[:12]}",
        evidence_type=EvidenceType.SOURCE_OBSERVATION,
        source_case_id=book_source_case_id,
        source_segment_id=book_source_segment_id,
        source_text_hash=series_memory_hash[:64],
        excerpt=f"Hydrated from Series {series_id} canonical fact: {source_record.canonical_name}",
        language="ko",
        observed_at=utc_now_iso(),
    )


def hydrate_book_store(
    series_store: SeriesMemoryStore,
    book_store: MemoryStore,
    book_identity: str,
    series_memory_hash: str,
) -> HydrationReport:
    """
    Copy Series canonical facts into BookMemoryStore as APPROVED records.

    READ-ONLY operation — does not mutate Series state.
    Conservative scope: only allowed fact types are hydrated.

    Conflict resolution:
    - No existing fact → Create new APPROVED record
    - Existing PENDING fact, same value → Upgrade to APPROVED
    - Existing PENDING fact, different value → Keep PENDING (requires user resolution)
    - Existing APPROVED fact, same value → DUPLICATE (no action)
    - Existing APPROVED fact, different value → CONFLICT (requires manual resolution)
    """
    hydrated_count = 0
    skipped_count = 0
    conflict_count = 0
    conflicts = []

    canonical_facts = series_store.get_all_canonical_facts()

    for series_record in canonical_facts:
        forbidden_reason = check_hydration_forbidden(series_record.fact_type)
        if forbidden_reason:
            skipped_count += 1
            continue

        character_id = hashlib.sha256(series_record.korean_name.encode("utf-8")).hexdigest()[:16]
        book_character_id = f"char_{character_id}"

        evidence = create_hydration_evidence(
            series_store.series_id, series_memory_hash, series_record,
            book_source_case_id="series_hydration",
            book_source_segment_id="hydration",
        )

        book_record = MemoryRecord(
            memory_id=hashlib.sha256(
                f"{book_character_id}|{series_record.fact_type.value}|{series_record.value}".encode()
            ).hexdigest()[:16],
            character_id=book_character_id,
            fact_type=series_record.fact_type,
            value=series_record.value,
            evidence=(evidence,),
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            confidence=series_record.confidence,
            approval_status=ApprovalStatus.APPROVED,
            source_language="ko",
            source_case_id="series_hydration",
            source_segment_id="hydration",
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
            version=1,
            expiry_policy=ExpiryPolicy(kind=ExpiryKind.NEVER),
            status=MemoryStatus.ACTIVE,
            approval_metadata=ApprovalMetadata(
                approved_value=series_record.value,
                approved_at=utc_now_iso(),
                reviewer="series_hydration",
                decision_reference=f"series:{series_store.series_id}:{series_memory_hash}",
            ),
            unresolved_identity=False,
            supersedes_memory_id=None,
        )

        try:
            result = add_or_merge_memory(book_store, book_record)
            if result.disposition in (AddDisposition.ACCEPTED, AddDisposition.MERGED):
                hydrated_count += 1
            elif result.disposition == AddDisposition.DUPLICATE:
                skipped_count += 1
            elif result.disposition == AddDisposition.CONFLICT:
                conflict_count += 1
                conflicts.append(f"CONFLICT: {series_record.series_character_id} {series_record.fact_type.value}")
            else:
                skipped_count += 1
        except Exception as e:
            skipped_count += 1
            conflicts.append(f"ERROR: {series_record.series_character_id} - {e}")

    hydration_source = f"series:{series_store.series_id}:{series_memory_hash}"

    return HydrationReport(
        series_id=series_store.series_id,
        book_identity=book_identity,
        hydrated_count=hydrated_count,
        skipped_count=skipped_count,
        conflict_count=conflict_count,
        hydration_source=hydration_source,
        conflicts=tuple(conflicts),
    )


def create_hydration_record(
    series_record: Any,
    book_identity: str,
    series_memory_hash: str,
) -> MemoryRecord:
    """Create a BookMemoryRecord from a SeriesCharacterRecord for hydration."""
    character_id = hashlib.sha256(series_record.korean_name.encode("utf-8")).hexdigest()[:16]
    book_character_id = f"char_{character_id}"

    evidence = create_hydration_evidence(series_record.series_id, series_memory_hash, series_record)

    return MemoryRecord(
        memory_id=hashlib.sha256(
            f"{book_character_id}|{series_record.fact_type.value}|{series_record.value}".encode()
        ).hexdigest()[:16],
        character_id=book_character_id,
        fact_type=series_record.fact_type,
        value=series_record.value,
        evidence=(evidence,),
        evidence_type=EvidenceType.SOURCE_OBSERVATION,
        confidence=series_record.confidence,
        approval_status=ApprovalStatus.APPROVED,
        source_language="ko",
        source_case_id="series_hydration",
        source_segment_id="hydration",
        created_at=utc_now_iso(),
        updated_at=utc_now_iso(),
        version=1,
        expiry_policy=ExpiryPolicy(kind=ExpiryKind.NEVER),
        status=MemoryStatus.ACTIVE,
        approval_metadata=ApprovalMetadata(
            approved_value=series_record.value,
            approved_at=utc_now_iso(),
            reviewer="series_hydration",
            decision_reference=f"series:{series_record.series_id}:{series_memory_hash}",
        ),
        unresolved_identity=False,
        supersedes_memory_id=None,
    )