from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Mapping, Optional, Tuple

if TYPE_CHECKING:
    from .store import SeriesMemoryStore
    from core.character_memory_v2.store import MemoryStore
else:
    from .store import SeriesMemoryStore
    from core.character_memory_v2.store import MemoryStore

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
from core.character_memory_v2.store import add_or_merge_memory

from .models import (
    SeriesCharacterRecord,
    SeriesFactRecord,
    PromotionRecord,
    AddResult,
    ConflictRecord,
)
from .validation import (
    ALLOWED_HYDRATION_FACT_TYPES,
    SeriesMemoryValidationError,
)

# Fact types eligible for promotion (NEVER-expiry, canonical facts)
PROMOTABLE_FACT_TYPES = frozenset({
    FactType.CANONICAL_NAME,
    FactType.NAME_VARIANT,
    FactType.RELATIONSHIP,
    FactType.ROLE_OR_IDENTITY,
    FactType.TERMINOLOGY_PREFERENCE,
    FactType.PRONOUN_OR_GENDER_REFERENCE,
    FactType.APPEARANCE,
})


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def promote_from_book(
    series_store: SeriesMemoryStore,
    book_store: MemoryStore,
    book_identity: str,
    approval_gate: bool = True,
) -> Tuple[AddResult, ...]:
    """
    Promote APPROVED facts from BookMemoryStore to SeriesMemoryStore.

    Requires MANUAL approval gate (frozen by D-07).
    Conflict detection: SAME value → NO-OP, DIFFERENT value → CONFLICT.
    Only APPROVED facts with promotable fact types are considered.
    """
    if approval_gate is False:
        raise SeriesMemoryValidationError(
            "Promotion requires MANUAL approval gate (D-07 frozen). "
            "Auto-promotion is not permitted."
        )

    results = []
    active_records = book_store.active_records()

    for book_record in active_records:
        if book_record.approval_status != ApprovalStatus.APPROVED:
            continue

        if book_record.fact_type not in PROMOTABLE_FACT_TYPES:
            continue

        # Skip facts that are not NEVER-expiry (transient/book-local)
        if book_record.expiry_policy.kind != ExpiryKind.NEVER:
            continue

        # Compute namespace-isolated series_character_id
        # Use Korean name (extracted from character_id) to match mapping's computation
        korean_name = book_record.character_id.replace("char_", "")
        series_character_id = hashlib.sha256(
            f"{series_store.series_id}|{korean_name}".encode()
        ).hexdigest()[:16]
        series_character_id = f"schar_{series_character_id}"

        # Check if series already has this fact
        existing_series_record = series_store.mapping.get_character(series_character_id)

        # Create promotion record
        promotion_id = hashlib.sha256(
            f"{series_store.series_id}|{book_identity}|{book_record.memory_id}|{utc_now_iso()}".encode()
        ).hexdigest()[:12]

        if existing_series_record is None:
            # No existing record → PROMOTE (create new)
            series_record = SeriesCharacterRecord(
                series_character_id=series_character_id,
                korean_name=book_record.character_id.replace("char_", ""),
                canonical_name=book_record.value if book_record.fact_type == FactType.CANONICAL_NAME else "",
                aliases=(book_record.value,) if book_record.fact_type == FactType.NAME_VARIANT else (),
                fact_type=book_record.fact_type,
                value=book_record.value,
                evidence=book_record.evidence,
                confidence=book_record.confidence,
                approval_status=ApprovalStatus.APPROVED,
                source_books=(book_identity,),
                created_at=book_record.created_at,
                updated_at=utc_now_iso(),
                version=1,
            )
            series_store.mapping.register_character(
                series_store.series_id,
                series_record.korean_name,
                series_record,
            )
            series_store._series_memory_hash = series_store._recompute_hash()

            promotion = PromotionRecord(
                promotion_id=promotion_id,
                series_id=series_store.series_id,
                book_identity=book_identity,
                source_memory_id=book_record.memory_id,
                target_series_character_id=series_character_id,
                fact_type=book_record.fact_type,
                action="created",
                resolved_by="user",
                resolved_at=utc_now_iso(),
                previous_value=None,
                new_value=book_record.value,
            )
            series_store._promotion_records.append(promotion)

            results.append(AddResult(
                disposition="created",
                record=series_record,
                message="New canonical fact promoted from book",
            ))

        elif existing_series_record.value == book_record.value:
            # Same value → NO-OP
            promotion = PromotionRecord(
                promotion_id=promotion_id,
                series_id=series_store.series_id,
                book_identity=book_identity,
                source_memory_id=book_record.memory_id,
                target_series_character_id=series_character_id,
                fact_type=book_record.fact_type,
                action="no_op",
                resolved_by="system",
                resolved_at=utc_now_iso(),
                previous_value=existing_series_record.value,
                new_value=book_record.value,
            )
            series_store._promotion_records.append(promotion)

            results.append(AddResult(
                disposition="no_op",
                record=existing_series_record,
                message="Same canonical value already exists in series",
            ))

        else:
            # Different value → CONFLICT (requires MANUAL resolution)
            conflict = ConflictRecord(
                conflict_id=hashlib.sha256(
                    f"{series_character_id}|{book_record.fact_type.value}|{book_record.value}|{existing_series_record.value}".encode()
                ).hexdigest()[:12],
                series_character_id=series_character_id,
                fact_type=book_record.fact_type,
                record_ids=(existing_series_record.series_character_id, series_character_id),
                created_at=utc_now_iso(),
            )

            promotion = PromotionRecord(
                promotion_id=promotion_id,
                series_id=series_store.series_id,
                book_identity=book_identity,
                source_memory_id=book_record.memory_id,
                target_series_character_id=series_character_id,
                fact_type=book_record.fact_type,
                action="conflict",
                resolved_by=None,
                resolved_at=utc_now_iso(),
                previous_value=existing_series_record.value,
                new_value=book_record.value,
            )
            series_store._promotion_records.append(promotion)

            results.append(AddResult(
                disposition="conflict",
                record=SeriesCharacterRecord(
                    series_character_id=series_character_id,
                    korean_name=book_record.character_id.replace("char_", ""),
                    canonical_name=book_record.value if book_record.fact_type == FactType.CANONICAL_NAME else "",
                    aliases=(book_record.value,) if book_record.fact_type == FactType.NAME_VARIANT else (),
                    fact_type=book_record.fact_type,
                    value=book_record.value,
                    evidence=book_record.evidence,
                    confidence=book_record.confidence,
                    approval_status=ApprovalStatus.APPROVED,
                    source_books=(book_identity,),
                    created_at=book_record.created_at,
                    updated_at=utc_now_iso(),
                    version=1,
                ),
                conflict=conflict,
                message="Conflicting canonical value requires MANUAL resolution",
            ))

    return tuple(results)


def resolve_promotion_conflict(
    series_store: SeriesMemoryStore,
    conflict: ConflictRecord,
    resolution: str,  # "book_wins" | "series_wins" | "manual"
    resolved_by: str,
    manual_value: Optional[str] = None,
) -> AddResult:
    """
    Resolve a promotion conflict.

    Args:
        series_store: The SeriesMemoryStore
        conflict: The conflict to resolve
        resolution: "book_wins", "series_wins", or "manual"
        resolved_by: Who resolved the conflict
        manual_value: If resolution is "manual", the chosen value

    Returns:
        AddResult with the resolved record
    """
    if conflict.resolution is not None:
        raise SeriesMemoryValidationError(f"Conflict {conflict.conflict_id} already resolved")

    # This is a placeholder for manual resolution logic
    # The actual implementation would update the conflict record
    # and potentially create/update the SeriesCharacterRecord
    raise NotImplementedError("Manual conflict resolution to be implemented in Batch 5.7+")