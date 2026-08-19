from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .canonical import compute_manifest_fingerprint, to_canonical_json
from .identity import SeriesIdentity, compute_series_id, canonicalize_series_key
from .manifest import (
    BookStatus,
    SeriesBookEntry,
    SeriesLifecycle,
    SeriesManifest,
    utc_now_iso,
)
from .persistence import load_manifest, save_manifest, get_series_dir, manifest_file_path
from .validation import validate_manifest, ValidationError, IntegrityError, ValidationResult


@dataclass(frozen=True)
class SeriesCreateResult:
    series_id: str
    manifest: SeriesManifest
    manifest_path: Path


@dataclass(frozen=True)
class BookAddResult:
    volume_number: int
    book_entry: SeriesBookEntry
    manifest: SeriesManifest
    manifest_path: Path


class SeriesRegistry:
    """
    Series Registry for creating, retrieving, and managing Series.

    All operations are fail-closed: validation errors raise exceptions,
    no partial state is persisted on failure.
    """

    def __init__(self, output_root: Path):
        self.output_root = output_root

    def create(self, user_defined_series_key: str, series_name: str | None = None) -> SeriesCreateResult:
        """
        Create a new Series.

        Args:
            user_defined_series_key: Stable key for deterministic series_id (canonicalized)
            series_name: Optional display name (defaults to stripped key)

        Returns:
            SeriesCreateResult with series_id, manifest, and manifest_path

        Raises:
            ValidationError: If series_id already exists
        """
        canonical_key = canonicalize_series_key(user_defined_series_key)
        series_id = compute_series_id(canonical_key)

        series_dir = get_series_dir(self.output_root, series_id)
        manifest_path = manifest_file_path(series_dir, series_id)

        if manifest_path.exists():
            raise ValidationError(f"Series already exists: {series_id}")

        identity = SeriesIdentity.create(user_defined_series_key, series_name)
        now = utc_now_iso()

        manifest = SeriesManifest(
            schema_name="ntpe.series_manifest",
            schema_version="1.0",
            series_id=identity.series_id,
            series_name=identity.series_name,
            lifecycle_status=SeriesLifecycle.CREATED,
            created_at=identity.created_at,
            updated_at=identity.updated_at,
            books=(),
            series_memory_hash="",
            series_checkpoint_hash="",
            series_entity_registry_hash="",
            manifest_fingerprint="",
        )

        # Add first book entry will transition to ACTIVE
        # For now, create with CREATED status
        fingerprint = compute_manifest_fingerprint(manifest.to_canonical_dict())
        manifest = manifest.with_fingerprint(fingerprint)

        save_manifest(manifest, manifest_path)

        return SeriesCreateResult(
            series_id=series_id,
            manifest=manifest,
            manifest_path=manifest_path,
        )

    def get(self, series_id: str) -> SeriesManifest:
        """
        Load SeriesManifest by series_id.

        Args:
            series_id: Series identifier

        Returns:
            SeriesManifest

        Raises:
            ValidationError: If not found or validation fails
        """
        series_dir = get_series_dir(self.output_root, series_id)
        manifest_path = manifest_file_path(series_dir, series_id)

        if not manifest_path.exists():
            raise ValidationError(f"Series not found: {series_id}")

        manifest = load_manifest(manifest_path)
        validate_manifest(manifest, series_id)
        return manifest

    def list_all(self) -> list[SeriesIdentity]:
        """List all series identities."""
        series_root = self.output_root / "series"
        if not series_root.exists():
            return []

        result = []
        for series_dir in series_root.iterdir():
            if series_dir.is_dir():
                manifest_path = manifest_file_path(series_dir, series_dir.name)
                if manifest_path.exists():
                    try:
                        manifest = load_manifest(manifest_path)
                        result.append(SeriesIdentity(
                            series_id=manifest.series_id,
                            series_name=manifest.series_name,
                            created_at=manifest.created_at,
                            updated_at=manifest.updated_at,
                        ))
                    except (ValidationError, IntegrityError):
                        pass  # Skip invalid manifests
        return sorted(result, key=lambda x: x.created_at)

    def add_book(
        self,
        series_id: str,
        book_identity: str,
        source_path: str,
        title: str,
        content_fingerprint: str,
        manifest_fingerprint: str,
    ) -> BookAddResult:
        """
        Add a book to an existing Series.

        Args:
            series_id: Target series identifier
            book_identity: Stage 4 Book ID
            source_path: Original source file path
            title: Display title for the book
            content_fingerprint: SHA256 of source file content
            manifest_fingerprint: BookIntakeManifest fingerprint

        Returns:
            BookAddResult with volume_number, book_entry, updated manifest

        Raises:
            ValidationError: If series not found, already archived, or book already member
        """
        manifest = self.get(series_id)

        if manifest.lifecycle_status == SeriesLifecycle.ARCHIVED:
            raise ValidationError(f"Cannot add book to archived series: {series_id}")

        if manifest.get_book_by_identity(book_identity) is not None:
            raise ValidationError(f"Book already member of series: {book_identity}")

        volume_number = manifest.next_volume_number()
        now = utc_now_iso()

        book_entry = SeriesBookEntry(
            volume_number=volume_number,
            book_identity=book_identity,
            source_path=source_path,
            title=title,
            status=BookStatus.PENDING,
            content_fingerprint=content_fingerprint,
            manifest_fingerprint=manifest_fingerprint,
            added_at=now,
        )

        updated_manifest = manifest.with_added_book(book_entry)
        fingerprint = compute_manifest_fingerprint(updated_manifest.to_canonical_dict())
        updated_manifest = updated_manifest.with_fingerprint(fingerprint)

        series_dir = get_series_dir(self.output_root, series_id)
        manifest_path = manifest_file_path(series_dir, series_id)
        save_manifest(updated_manifest, manifest_path)

        return BookAddResult(
            volume_number=volume_number,
            book_entry=book_entry,
            manifest=updated_manifest,
            manifest_path=manifest_path,
        )

    def update_name(self, series_id: str, new_series_name: str) -> SeriesManifest:
        """
        Update series display name (series_id remains unchanged).

        Args:
            series_id: Series identifier
            new_series_name: New display name

        Returns:
            Updated SeriesManifest

        Raises:
            ValidationError: If series not found or archived
        """
        manifest = self.get(series_id)

        if manifest.lifecycle_status == SeriesLifecycle.ARCHIVED:
            raise ValidationError(f"Cannot rename archived series: {series_id}")

        updated_manifest = manifest.with_updated_name(new_series_name.strip())
        fingerprint = compute_manifest_fingerprint(updated_manifest.to_canonical_dict())
        updated_manifest = updated_manifest.with_fingerprint(fingerprint)

        series_dir = get_series_dir(self.output_root, series_id)
        manifest_path = manifest_file_path(series_dir, series_id)
        save_manifest(updated_manifest, manifest_path)

        return updated_manifest

    def set_book_status(self, series_id: str, volume_number: int, new_status: BookStatus) -> SeriesManifest:
        """
        Update book status within series.

        Validates state transitions per BookStatus machine.

        Args:
            series_id: Series identifier
            volume_number: Book volume number
            new_status: New book status

        Returns:
            Updated SeriesManifest

        Raises:
            ValidationError: If invalid transition or series/book not found
        """
        manifest = self.get(series_id)

        book = manifest.get_book(volume_number)
        if book is None:
            raise ValidationError(f"Book not found in series: volume={volume_number}")

        # Validate state transition
        valid_transitions = {
            BookStatus.PENDING: {BookStatus.IN_PROGRESS, BookStatus.FAILED, BookStatus.ARCHIVED},
            BookStatus.IN_PROGRESS: {BookStatus.COMPLETED, BookStatus.FAILED, BookStatus.ARCHIVED},
            BookStatus.COMPLETED: {BookStatus.PROMOTED, BookStatus.ARCHIVED},
            BookStatus.PROMOTED: {BookStatus.ARCHIVED},
            BookStatus.FAILED: {BookStatus.ARCHIVED},
            BookStatus.ARCHIVED: set(),  # Terminal
        }

        if new_status not in valid_transitions.get(book.status, set()):
            raise ValidationError(
                f"Invalid book status transition: {book.status.value} -> {new_status.value}"
            )

        updated_manifest = manifest.with_updated_book_status(volume_number, new_status)

        # Auto-transition series lifecycle
        if updated_manifest.all_books_promoted() and not updated_manifest.has_in_progress_books():
            if updated_manifest.lifecycle_status == SeriesLifecycle.ACTIVE:
                # Note: lifecycle_status is part of frozen dataclass, need to recreate
                # This is handled by creating new manifest
                pass  # Will be handled by caller if needed

        fingerprint = compute_manifest_fingerprint(updated_manifest.to_canonical_dict())
        updated_manifest = updated_manifest.with_fingerprint(fingerprint)

        series_dir = get_series_dir(self.output_root, series_id)
        manifest_path = manifest_file_path(series_dir, series_id)
        save_manifest(updated_manifest, manifest_path)

        return updated_manifest

    def archive(self, series_id: str) -> SeriesManifest:
        """
        Archive a series (read-only, no new books accepted).

        Args:
            series_id: Series identifier

        Returns:
            Updated SeriesManifest with ARCHIVED status

        Raises:
            ValidationError: If series not found
        """
        manifest = self.get(series_id)

        if manifest.lifecycle_status == SeriesLifecycle.ARCHIVED:
            return manifest  # Already archived

        # Note: SeriesLifecycle is frozen, need to recreate manifest
        updated_manifest = SeriesManifest(
            schema_name=manifest.schema_name,
            schema_version=manifest.schema_version,
            series_id=manifest.series_id,
            series_name=manifest.series_name,
            lifecycle_status=SeriesLifecycle.ARCHIVED,
            created_at=manifest.created_at,
            updated_at=utc_now_iso(),
            books=manifest.books,
            series_memory_hash=manifest.series_memory_hash,
            series_checkpoint_hash=manifest.series_checkpoint_hash,
            series_entity_registry_hash=manifest.series_entity_registry_hash,
            manifest_fingerprint="",
        )

        fingerprint = compute_manifest_fingerprint(updated_manifest.to_canonical_dict())
        updated_manifest = updated_manifest.with_fingerprint(fingerprint)

        series_dir = get_series_dir(self.output_root, series_id)
        manifest_path = manifest_file_path(series_dir, series_id)
        save_manifest(updated_manifest, manifest_path)

        return updated_manifest

    def update_series_memory_hash(self, series_id: str, memory_hash: str) -> SeriesManifest:
        """Update series_memory_hash after promotion."""
        manifest = self.get(series_id)
        updated_manifest = manifest.with_series_memory_hash(memory_hash)
        fingerprint = compute_manifest_fingerprint(updated_manifest.to_canonical_dict())
        updated_manifest = updated_manifest.with_fingerprint(fingerprint)

        series_dir = get_series_dir(self.output_root, series_id)
        manifest_path = manifest_file_path(series_dir, series_id)
        save_manifest(updated_manifest, manifest_path)

        return updated_manifest

    def update_series_entity_registry_hash(self, series_id: str, registry_hash: str) -> SeriesManifest:
        """Update series_entity_registry_hash after registry changes."""
        manifest = self.get(series_id)
        updated_manifest = manifest.with_series_entity_registry_hash(registry_hash)
        fingerprint = compute_manifest_fingerprint(updated_manifest.to_canonical_dict())
        updated_manifest = updated_manifest.with_fingerprint(fingerprint)

        series_dir = get_series_dir(self.output_root, series_id)
        manifest_path = manifest_file_path(series_dir, series_id)
        save_manifest(updated_manifest, manifest_path)

        return updated_manifest
