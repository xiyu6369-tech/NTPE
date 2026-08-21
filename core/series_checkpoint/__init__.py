"""P0 Stage 5 Batch 5.6 — Series Checkpoint Hierarchy.

Series-level checkpoint orchestration unifying Series artifacts and
references to existing frozen checkpoint systems.
"""

from __future__ import annotations

from .models import (
    SeriesCheckpoint,
    BookCheckpointRef,
    SessionCheckpointRef,
    CheckpointCreationReport,
    SeriesResumeReport,
    BookResumeReport,
    BookStartReport,
    BookResumeInfo,
    compute_series_checkpoint_fingerprint,
    to_canonical_json,
)
from .manager import SeriesCheckpointManager
from .persistence import (
    get_series_checkpoint_path,
    save_series_checkpoint,
    load_series_checkpoint_from_path,
    load_latest_series_checkpoint,
)
from .recovery import (
    resume_series,
    resume_book_in_series,
    start_new_book_in_series,
)
from .validation import (
    SeriesCheckpointValidationError,
    SeriesCheckpointIntegrityError,
    SeriesCheckpointBookHashMismatchError,
    SeriesCheckpointSessionMismatchError,
    validate_series_checkpoint_schema,
    validate_series_checkpoint_integrity,
    validate_series_checkpoint_full,
    validate_cross_series_isolation,
)

__all__ = [
    # Models
    "SeriesCheckpoint",
    "BookCheckpointRef",
    "SessionCheckpointRef",
    "CheckpointCreationReport",
    "SeriesResumeReport",
    "BookResumeReport",
    "BookStartReport",
    "BookResumeInfo",
    "compute_series_checkpoint_fingerprint",
    "to_canonical_json",
    # Manager
    "SeriesCheckpointManager",
    # Persistence
    "get_series_checkpoint_path",
    "save_series_checkpoint",
    "load_series_checkpoint_from_path",
    "load_latest_series_checkpoint",
    # Recovery
    "resume_series",
    "resume_book_in_series",
    "start_new_book_in_series",
    # Validation
    "SeriesCheckpointValidationError",
    "SeriesCheckpointIntegrityError",
    "SeriesCheckpointBookHashMismatchError",
    "SeriesCheckpointSessionMismatchError",
    "validate_series_checkpoint_schema",
    "validate_series_checkpoint_integrity",
    "validate_series_checkpoint_full",
    "validate_cross_series_isolation",
]

__version__ = "p0-stage5-batch5.6"