from __future__ import annotations

from .canonical import (
    to_canonical_json,
    compute_sha256,
    compute_manifest_fingerprint,
    compute_series_fingerprint,
)
from .contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    MANIFEST_FILENAME_TEMPLATE,
    SERIES_DIR_NAME,
    BOOKS_DIR_NAME,
    DEFAULT_PROJECT_NAME,
)
from .identity import (
    SeriesIdentity,
    compute_series_id,
    canonicalize_series_key,
    utc_now_iso,
)
from .manifest import (
    SeriesLifecycle,
    BookStatus,
    SeriesBookEntry,
    SeriesManifest,
    utc_now_iso,
)
from .persistence import (
    get_series_dir,
    manifest_file_path,
    save_manifest,
    load_manifest,
    ensure_series_dir,
)
from .registry import (
    SeriesRegistry,
    SeriesCreateResult,
    BookAddResult,
)
from .validation import (
    ValidationError,
    IntegrityError,
    ValidationResult,
    validate_manifest,
    validate_series_create,
)

__all__ = [
    # canonical
    "to_canonical_json",
    "compute_sha256",
    "compute_manifest_fingerprint",
    "compute_series_fingerprint",
    # contract
    "SCHEMA_NAME",
    "SCHEMA_VERSION",
    "MANIFEST_FILENAME_TEMPLATE",
    "SERIES_DIR_NAME",
    "BOOKS_DIR_NAME",
    "DEFAULT_PROJECT_NAME",
    # identity
    "SeriesIdentity",
    "compute_series_id",
    "canonicalize_series_key",
    "utc_now_iso",
    # manifest
    "SeriesLifecycle",
    "BookStatus",
    "SeriesBookEntry",
    "SeriesManifest",
    # persistence
    "get_series_dir",
    "manifest_file_path",
    "save_manifest",
    "load_manifest",
    "ensure_series_dir",
    # registry
    "SeriesRegistry",
    "SeriesCreateResult",
    "BookAddResult",
    # validation
    "ValidationError",
    "IntegrityError",
    "ValidationResult",
    "validate_manifest",
    "validate_series_create",
]