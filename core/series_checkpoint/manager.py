"""P0 Stage 5 Batch 5.6 — Series Checkpoint Manager.

Orchestrates Series checkpoint creation, persistence, and validation.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Optional

from .models import (
    SeriesCheckpoint,
    BookCheckpointRef,
    CheckpointCreationReport,
    _generate_checkpoint_id,
    compute_series_checkpoint_fingerprint,
)
from .persistence import get_series_checkpoint_path, save_series_checkpoint
from .validation import validate_series_checkpoint_full, validate_cross_series_isolation


class SeriesCheckpointManager:
    """Orchestrate Series checkpoint creation, persistence, and validation."""

    version = "p0-stage5-batch5.6"

    def __init__(
        self,
        output_root: Path,
        series_registry: Any,  # SeriesRegistry from core.series_identity
        series_memory_store: Any,  # SeriesMemoryStore from core.series_memory
        series_entity_registry: Any,  # SeriesEntityRegistry from core.series_entity_registry
        series_glossary: Any,  # SeriesGlossary from core.glossary_builder
        series_knowledge: Any,  # SeriesKnowledge from core.knowledge_runtime.loader
    ):
        self.output_root = output_root
        self.series_registry = series_registry
        self.series_memory_store = series_memory_store
        self.series_entity_registry = series_entity_registry
        self.series_glossary = series_glossary
        self.series_knowledge = series_knowledge

    def create_checkpoint(
        self,
        series_id: str,
        include_completed_books: bool = True,
    ) -> CheckpointCreationReport:
        """
        Create a new SeriesCheckpoint aggregating all current state.

        Called after:
        - Book promotion completed (series memory/glossary/knowledge updated)
        - Manual series-level save requested
        """
        # Validate cross-series isolation
        validate_cross_series_isolation(
            SeriesCheckpoint(series_id=series_id, checkpoint_id="dummy"),
            series_id,
        )

        # Get SeriesManifest for book list and manifest fingerprint
        series_manifest = self.series_registry.get(series_id)

        # Collect Series artifact hashes
        series_memory_hash = getattr(self.series_memory_store, "series_memory_hash", "")
        series_entity_registry_hash = getattr(self.series_entity_registry, "series_entity_registry_hash", "")
        series_glossary_hash = getattr(self.series_glossary, "glossary_hash", "")
        series_knowledge_hash = getattr(self.series_knowledge, "knowledge_hash", "")

        # Build book checkpoint references
        book_checkpoints = []
        session_checkpoints_total = 0

        for book_entry in series_manifest.books:
            if not include_completed_books and book_entry.status.value in ("completed", "promoted", "archived"):
                continue

            # Get book memory hash
            from core.character_memory_v2.persistence import get_memory_file_path
            memory_path = get_memory_file_path(self.output_root, book_entry.book_identity)
            book_memory_hash = ""
            if memory_path.exists():
                book_memory_hash = hashlib.sha256(memory_path.read_bytes()).hexdigest()

            # Get book context hash
            from core.context_scene_memory.persistence import get_context_memory_file_path
            context_path = get_context_memory_file_path(self.output_root, book_entry.book_identity)
            book_context_hash = ""
            if context_path.exists():
                book_context_hash = hashlib.sha256(context_path.read_bytes()).hexdigest()

            # Get latest session checkpoint ID (if available from runtime checkpoint manager)
            latest_session_checkpoint_id = self._get_latest_session_checkpoint_id(book_entry.book_identity)

            book_ref = BookCheckpointRef(
                book_identity=book_entry.book_identity,
                volume_number=book_entry.volume_number,
                book_memory_hash=book_memory_hash,
                book_context_hash=book_context_hash,
                latest_session_checkpoint_id=latest_session_checkpoint_id,
                status=book_entry.status.value,
            )
            book_checkpoints.append(book_ref)

            if latest_session_checkpoint_id:
                session_checkpoints_total += 1

        # Create checkpoint
        checkpoint = SeriesCheckpoint(
            schema_name="ntpe.series_checkpoint",
            schema_version="1.0",
            series_id=series_id,
            checkpoint_id=_generate_checkpoint_id(series_id),
            created_at=self._utc_now_iso(),
            series_memory_hash=series_memory_hash,
            series_entity_registry_hash=series_entity_registry_hash,
            series_glossary_hash=series_glossary_hash,
            series_knowledge_hash=series_knowledge_hash,
            manifest_fingerprint=series_manifest.manifest_fingerprint,
            book_checkpoints=tuple(book_checkpoints),
            state_hash="",  # Will be computed by with_hash()
        )

        # Compute state_hash
        checkpoint = checkpoint.with_hash()

        # Persist
        checkpoint_path = get_series_checkpoint_path(self.output_root, series_id)
        save_series_checkpoint(checkpoint, checkpoint_path)

        # Update manifest with checkpoint hash (derived state - one-way)
        self.series_registry.update_series_checkpoint_hash(series_id, checkpoint.state_hash)

        return CheckpointCreationReport(
            series_id=series_id,
            checkpoint_id=checkpoint.checkpoint_id,
            created_at=checkpoint.created_at,
            state_hash=checkpoint.state_hash,
            book_checkpoints_count=len(book_checkpoints),
            session_checkpoints_total=session_checkpoints_total,
            manifest_fingerprint=series_manifest.manifest_fingerprint,
        )

    def _get_latest_session_checkpoint_id(self, book_identity: str) -> Optional[str]:
        """Get latest session checkpoint ID for a book from runtime checkpoint manager.

        Note: RuntimeCheckpointManager is in-memory only (RM-6.3.2 frozen).
        Returns None if not available in current process.
        """
        try:
            from core.runtime_checkpoint.manager import RuntimeCheckpointManager
            # The runtime checkpoint manager is typically accessed through the runtime orchestrator
            # For now, return None - session checkpoint IDs would be captured during active translation
            return None
        except ImportError:
            return None

    def _utc_now_iso(self) -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def save_checkpoint(self, checkpoint: SeriesCheckpoint) -> Path:
        """Persist SeriesCheckpoint to disk with atomic write."""
        checkpoint_path = get_series_checkpoint_path(self.output_root, checkpoint.series_id)
        save_series_checkpoint(checkpoint, checkpoint_path)
        return checkpoint_path

    def load_latest_checkpoint(self, series_id: str) -> Optional[SeriesCheckpoint]:
        """Load latest SeriesCheckpoint for series, or None if not found."""
        from .persistence import load_latest_series_checkpoint
        return load_latest_series_checkpoint(series_id, self.output_root)

    def validate_checkpoint(self, series_id: str) -> None:
        """Validate all hashes in checkpoint against actual files (fail-closed)."""
        checkpoint = self.load_latest_checkpoint(series_id)
        if checkpoint is None:
            raise SeriesCheckpointIntegrityError(series_id, "No checkpoint found")

        series_manifest = self.series_registry.get(series_id)
        validate_series_checkpoint_full(checkpoint, self.output_root, series_manifest)
        validate_cross_series_isolation(checkpoint, series_id)


# Need to import the exception for use in validate_checkpoint
from .validation import SeriesCheckpointIntegrityError
