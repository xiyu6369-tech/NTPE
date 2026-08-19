"""P0 Stage 5 Batch 5.3 — Series Entity Registry.

Persistent Series-level entity registry with namespace isolation.
Integrates with EntityResolver via existing user_overrides extension point.
"""

from .models import (
    SeriesEntityRecord,
    EntityPromotionRecord,
    AddResult,
    ConflictRecord,
    HydrationReport,
    compute_series_entity_id,
)

from .registry import SeriesEntityRegistry
from .persistence import (
    save_series_entity_registry,
    load_series_entity_registry,
    get_series_entity_registry_path,
    verify_series_entity_registry_integrity,
    create_empty_series_entity_registry,
)
from .validation import (
    validate_series_entity_record,
    verify_series_entity_registry_fingerprint,
    compute_series_entity_registry_fingerprint,
    to_canonical_json,
    SeriesEntityValidationError,
    SeriesEntityIntegrityError,
)
from .integration import hydrate_resolver_from_series

__all__ = [
    # Models
    "SeriesEntityRecord",
    "EntityPromotionRecord",
    "AddResult",
    "ConflictRecord",
    "HydrationReport",
    "compute_series_entity_id",
    # Registry
    "SeriesEntityRegistry",
    # Persistence
    "save_series_entity_registry",
    "load_series_entity_registry",
    "get_series_entity_registry_path",
    "verify_series_entity_registry_integrity",
    "create_empty_series_entity_registry",
    # Validation
    "validate_series_entity_record",
    "verify_series_entity_registry_fingerprint",
    "compute_series_entity_registry_fingerprint",
    "to_canonical_json",
    "SeriesEntityValidationError",
    "SeriesEntityIntegrityError",
    # Integration
    "hydrate_resolver_from_series",
]