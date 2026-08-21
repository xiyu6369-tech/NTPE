"""P0 Stage 5 Batch 5.6 — Series Checkpoint Validation.

Schema validation, integrity verification, and fail-closed exceptions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import SeriesCheckpoint, compute_series_checkpoint_fingerprint


class SeriesCheckpointValidationError(Exception):
    """Raised when SeriesCheckpoint schema validation fails."""
    pass


class SeriesCheckpointIntegrityError(Exception):
    """Raised when SeriesCheckpoint fingerprint verification fails (fail-closed)."""
    def __init__(self, checkpoint_id: str, detail: str):
        super().__init__(f"Integrity check failed for checkpoint {checkpoint_id}: {detail}")
        self.checkpoint_id = checkpoint_id


class SeriesCheckpointBookHashMismatchError(Exception):
    """Raised when book memory/context hash doesn't match actual file."""
    pass


class SeriesCheckpointSessionMismatchError(Exception):
    """Raised when session checkpoint reference doesn't match."""
    pass


def validate_series_checkpoint_schema(checkpoint: SeriesCheckpoint) -> None:
    """Validate SeriesCheckpoint schema (fail-closed)."""
    if checkpoint.schema_name != "ntpe.series_checkpoint":
        raise SeriesCheckpointValidationError(f"Invalid schema_name: {checkpoint.schema_name}")
    if checkpoint.schema_version != "1.0":
        raise SeriesCheckpointValidationError(f"Invalid schema_version: {checkpoint.schema_version}")
    if not checkpoint.series_id:
        raise SeriesCheckpointValidationError("series_id is required")
    if not checkpoint.checkpoint_id:
        raise SeriesCheckpointValidationError("checkpoint_id is required")
    if not checkpoint.checkpoint_id.startswith("scheck_"):
        raise SeriesCheckpointValidationError(f"Invalid checkpoint_id format: {checkpoint.checkpoint_id}")
    if not checkpoint.created_at:
        raise SeriesCheckpointValidationError("created_at is required")
    if not isinstance(checkpoint.book_checkpoints, tuple):
        raise SeriesCheckpointValidationError("book_checkpoints must be a tuple")


def validate_series_checkpoint_integrity(checkpoint: SeriesCheckpoint) -> None:
    """Validate SeriesCheckpoint fingerprint integrity (fail-closed)."""
    if not checkpoint.state_hash:
        raise SeriesCheckpointIntegrityError(checkpoint.checkpoint_id, "state_hash is empty")
    computed = compute_series_checkpoint_fingerprint(checkpoint.to_canonical_dict())
    if checkpoint.state_hash != computed:
        raise SeriesCheckpointIntegrityError(
            checkpoint.checkpoint_id,
            f"state_hash mismatch: stored={checkpoint.state_hash}, computed={computed}"
        )


def validate_book_checkpoint_refs(
    checkpoint: SeriesCheckpoint,
    output_root: Path,
    series_manifest: Any,  # SeriesManifest - avoid circular import
) -> None:
    """Validate all book checkpoint references against actual files."""
    from core.character_memory_v2.persistence import get_memory_file_path
    from core.context_scene_memory.persistence import get_context_memory_file_path

    for book_ref in checkpoint.book_checkpoints:
        # Validate book exists in manifest
        book_entry = series_manifest.get_book_by_identity(book_ref.book_identity)
        if book_entry is None:
            raise SeriesCheckpointBookHashMismatchError(
                f"Book {book_ref.book_identity} not found in SeriesManifest"
            )

        # Validate book memory hash
        memory_path = get_memory_file_path(output_root, book_ref.book_identity)
        if memory_path.exists():
            import hashlib
            actual_hash = hashlib.sha256(memory_path.read_bytes()).hexdigest()
            if book_ref.book_memory_hash != actual_hash:
                raise SeriesCheckpointBookHashMismatchError(
                    f"Book memory hash mismatch for {book_ref.book_identity}: "
                    f"expected={book_ref.book_memory_hash}, actual={actual_hash}"
                )

        # Validate book context hash
        context_path = get_context_memory_file_path(output_root, book_ref.book_identity)
        if context_path.exists():
            import hashlib
            actual_hash = hashlib.sha256(context_path.read_bytes()).hexdigest()
            if book_ref.book_context_hash != actual_hash:
                raise SeriesCheckpointBookHashMismatchError(
                    f"Book context hash mismatch for {book_ref.book_identity}: "
                    f"expected={book_ref.book_context_hash}, actual={actual_hash}"
                )


def validate_session_checkpoint_refs(
    checkpoint: SeriesCheckpoint,
) -> None:
    """Validate session checkpoint references format (no cross-process validation - runtime_checkpoint is in-memory)."""
    for book_ref in checkpoint.book_checkpoints:
        if book_ref.latest_session_checkpoint_id:
            # Format validation only - runtime_checkpoint is in-memory (RM-6.3.2 frozen)
            session_id = book_ref.latest_session_checkpoint_id
            if not session_id or not isinstance(session_id, str):
                raise SeriesCheckpointSessionMismatchError(
                    f"Invalid session checkpoint ID format: {session_id}"
                )


def validate_series_checkpoint_full(
    checkpoint: SeriesCheckpoint,
    output_root: Path,
    series_manifest: Any,
) -> None:
    """Complete validation: schema, integrity, book refs, session refs format."""
    validate_series_checkpoint_schema(checkpoint)
    validate_series_checkpoint_integrity(checkpoint)
    validate_book_checkpoint_refs(checkpoint, output_root, series_manifest)
    validate_session_checkpoint_refs(checkpoint)


def validate_cross_series_isolation(
    checkpoint: SeriesCheckpoint,
    expected_series_id: str,
) -> None:
    """Validate cross-series isolation (fail-closed)."""
    if checkpoint.series_id != expected_series_id:
        raise SeriesCheckpointValidationError(
            f"Series ID mismatch: expected {expected_series_id}, got {checkpoint.series_id}"
        )
    # Verify checkpoint_id contains series namespace
    if not checkpoint.checkpoint_id.startswith("scheck_"):
        raise SeriesCheckpointValidationError("Checkpoint ID does not follow series namespace format")