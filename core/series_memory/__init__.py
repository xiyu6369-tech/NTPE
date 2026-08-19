"""Series Memory Store — Canonical Series-level character facts.

This package provides the Series Memory Store for P0 Stage 5 Series Continuity.
It implements canonical fact storage, persistence, hydration, and promotion
with namespace isolation and fail-closed integrity.
"""

from .models import (
    SeriesCharacterRecord,
    SeriesFactRecord,
    AddResult,
    ConflictRecord,
    PromotionRecord,
    HydrationReport,
)
from .store import SeriesMemoryStore, create_series_character_record
from .persistence import (
    get_series_dir,
    series_memory_file_path,
    save_series_memory,
    load_series_memory,
    verify_series_memory_integrity,
    create_empty_series_memory,
    ensure_series_dir,
)
from .hydration import hydrate_book_store, create_hydration_record
from .promotion import promote_from_book
from .validation import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    validate_series_character_record,
    validate_series_fact_record,
    validate_series_memory_payload,
    validate_hydration_scope,
    check_hydration_forbidden,
    verify_fingerprint,
    compute_series_memory_fingerprint,
    to_canonical_json,
    SeriesMemoryValidationError,
    SeriesMemoryIntegrityError,
    ValidationReport,
)
from .mapping import (
    SeriesNamespaceMapping,
    compute_series_character_id,
    compute_series_fact_id,
    validate_namespace_isolation,
)

__all__ = [
    "SeriesCharacterRecord",
    "SeriesFactRecord",
    "AddResult",
    "ConflictRecord",
    "PromotionRecord",
    "HydrationReport",
    "SeriesMemoryStore",
    "create_series_character_record",
    "get_series_dir",
    "series_memory_file_path",
    "save_series_memory",
    "load_series_memory",
    "verify_series_memory_integrity",
    "create_empty_series_memory",
    "ensure_series_dir",
    "hydrate_book_store",
    "create_hydration_record",
    "promote_from_book",
    "SCHEMA_NAME",
    "SCHEMA_VERSION",
    "validate_series_character_record",
    "validate_series_fact_record",
    "validate_series_memory_payload",
    "validate_hydration_scope",
    "check_hydration_forbidden",
    "verify_fingerprint",
    "compute_series_memory_fingerprint",
    "to_canonical_json",
    "SeriesMemoryValidationError",
    "SeriesMemoryIntegrityError",
    "ValidationReport",
    "SeriesNamespaceMapping",
    "compute_series_character_id",
    "compute_series_fact_id",
    "validate_namespace_isolation",
]