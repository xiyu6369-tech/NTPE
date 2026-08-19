from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class SeriesLifecycle(str, Enum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class BookStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PROMOTED = "promoted"
    ARCHIVED = "archived"
    FAILED = "failed"


@dataclass(frozen=True)
class SeriesBookEntry:
    volume_number: int
    book_identity: str
    source_path: str
    title: str
    status: BookStatus
    content_fingerprint: str
    manifest_fingerprint: str
    added_at: str
    completed_at: str | None = None
    promoted_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "volume_number": self.volume_number,
            "book_identity": self.book_identity,
            "source_path": self.source_path,
            "title": self.title,
            "status": self.status.value,
            "content_fingerprint": self.content_fingerprint,
            "manifest_fingerprint": self.manifest_fingerprint,
            "added_at": self.added_at,
            "completed_at": self.completed_at,
            "promoted_at": self.promoted_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SeriesBookEntry":
        return cls(
            volume_number=int(data["volume_number"]),
            book_identity=str(data["book_identity"]),
            source_path=str(data["source_path"]),
            title=str(data["title"]),
            status=BookStatus(data["status"]),
            content_fingerprint=str(data["content_fingerprint"]),
            manifest_fingerprint=str(data["manifest_fingerprint"]),
            added_at=str(data["added_at"]),
            completed_at=data.get("completed_at") if data.get("completed_at") is not None else None,
            promoted_at=data.get("promoted_at") if data.get("promoted_at") is not None else None,
        )

    def with_status(self, new_status: BookStatus, now: str | None = None) -> "SeriesBookEntry":
        """Return new entry with updated status and timestamp."""
        timestamp = now or utc_now_iso()
        completed_at = self.completed_at
        promoted_at = self.promoted_at
        if new_status == BookStatus.COMPLETED and self.completed_at is None:
            completed_at = timestamp
        if new_status == BookStatus.PROMOTED and self.promoted_at is None:
            promoted_at = timestamp
        return SeriesBookEntry(
            volume_number=self.volume_number,
            book_identity=self.book_identity,
            source_path=self.source_path,
            title=self.title,
            status=new_status,
            content_fingerprint=self.content_fingerprint,
            manifest_fingerprint=self.manifest_fingerprint,
            added_at=self.added_at,
            completed_at=completed_at,
            promoted_at=promoted_at,
        )


@dataclass(frozen=True)
class SeriesManifest:
    schema_name: str
    schema_version: str
    series_id: str
    series_name: str
    lifecycle_status: SeriesLifecycle
    created_at: str
    updated_at: str
    books: tuple[SeriesBookEntry, ...]
    series_memory_hash: str
    series_checkpoint_hash: str
    series_entity_registry_hash: str
    manifest_fingerprint: str

    def to_dict(self, include_manifest_fingerprint: bool = True) -> dict[str, Any]:
        payload = {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "series_id": self.series_id,
            "series_name": self.series_name,
            "lifecycle_status": self.lifecycle_status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "books": [book.to_dict() for book in self.books],
            "series_memory_hash": self.series_memory_hash,
            "series_checkpoint_hash": self.series_checkpoint_hash,
            "series_entity_registry_hash": self.series_entity_registry_hash,
        }
        if include_manifest_fingerprint:
            payload["manifest_fingerprint"] = self.manifest_fingerprint
        return payload

    def to_canonical_dict(self) -> dict[str, Any]:
        """Return canonical dict for fingerprint computation (excludes manifest_fingerprint)."""
        return self.to_dict(include_manifest_fingerprint=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SeriesManifest":
        books = tuple(SeriesBookEntry.from_dict(b) for b in data.get("books", []))
        return cls(
            schema_name=data["schema_name"],
            schema_version=data["schema_version"],
            series_id=data["series_id"],
            series_name=data["series_name"],
            lifecycle_status=SeriesLifecycle(data["lifecycle_status"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            books=books,
            series_memory_hash=data.get("series_memory_hash", ""),
            series_checkpoint_hash=data.get("series_checkpoint_hash", ""),
            series_entity_registry_hash=data.get("series_entity_registry_hash", ""),
            manifest_fingerprint=data.get("manifest_fingerprint", ""),
        )

    def get_book(self, volume_number: int) -> SeriesBookEntry | None:
        for book in self.books:
            if book.volume_number == volume_number:
                return book
        return None

    def get_book_by_identity(self, book_identity: str) -> SeriesBookEntry | None:
        for book in self.books:
            if book.book_identity == book_identity:
                return book
        return None

    def next_volume_number(self) -> int:
        if not self.books:
            return 1
        return max(book.volume_number for book in self.books) + 1

    def has_in_progress_books(self) -> bool:
        return any(b.status == BookStatus.IN_PROGRESS for b in self.books)

    def all_books_promoted(self) -> bool:
        if not self.books:
            return False
        return all(b.status == BookStatus.PROMOTED for b in self.books)

    def with_updated_name(self, new_name: str) -> "SeriesManifest":
        return SeriesManifest(
            schema_name=self.schema_name,
            schema_version=self.schema_version,
            series_id=self.series_id,
            series_name=new_name,
            lifecycle_status=self.lifecycle_status,
            created_at=self.created_at,
            updated_at=utc_now_iso(),
            books=self.books,
            series_memory_hash=self.series_memory_hash,
            series_checkpoint_hash=self.series_checkpoint_hash,
            series_entity_registry_hash=self.series_entity_registry_hash,
            manifest_fingerprint="",  # Will be recomputed
        )

    def with_added_book(self, book_entry: SeriesBookEntry) -> "SeriesManifest":
        new_books = tuple(sorted(self.books + (book_entry,), key=lambda b: b.volume_number))
        return SeriesManifest(
            schema_name=self.schema_name,
            schema_version=self.schema_version,
            series_id=self.series_id,
            series_name=self.series_name,
            lifecycle_status=SeriesLifecycle.ACTIVE,
            created_at=self.created_at,
            updated_at=utc_now_iso(),
            books=new_books,
            series_memory_hash=self.series_memory_hash,
            series_checkpoint_hash=self.series_checkpoint_hash,
            series_entity_registry_hash=self.series_entity_registry_hash,
            manifest_fingerprint="",
        )

    def with_updated_book_status(self, volume_number: int, new_status: BookStatus) -> "SeriesManifest":
        new_books = []
        for book in self.books:
            if book.volume_number == volume_number:
                new_books.append(book.with_status(new_status))
            else:
                new_books.append(book)
        new_books.sort(key=lambda b: b.volume_number)
        return SeriesManifest(
            schema_name=self.schema_name,
            schema_version=self.schema_version,
            series_id=self.series_id,
            series_name=self.series_name,
            lifecycle_status=self.lifecycle_status,
            created_at=self.created_at,
            updated_at=utc_now_iso(),
            books=tuple(new_books),
            series_memory_hash=self.series_memory_hash,
            series_checkpoint_hash=self.series_checkpoint_hash,
            series_entity_registry_hash=self.series_entity_registry_hash,
            manifest_fingerprint="",
        )

    def with_series_memory_hash(self, hash_value: str) -> "SeriesManifest":
        return SeriesManifest(
            schema_name=self.schema_name,
            schema_version=self.schema_version,
            series_id=self.series_id,
            series_name=self.series_name,
            lifecycle_status=self.lifecycle_status,
            created_at=self.created_at,
            updated_at=utc_now_iso(),
            books=self.books,
            series_memory_hash=hash_value,
            series_checkpoint_hash=self.series_checkpoint_hash,
            series_entity_registry_hash=self.series_entity_registry_hash,
            manifest_fingerprint="",
        )

    def with_series_checkpoint_hash(self, hash_value: str) -> "SeriesManifest":
        return SeriesManifest(
            schema_name=self.schema_name,
            schema_version=self.schema_version,
            series_id=self.series_id,
            series_name=self.series_name,
            lifecycle_status=self.lifecycle_status,
            created_at=self.created_at,
            updated_at=utc_now_iso(),
            books=self.books,
            series_memory_hash=self.series_memory_hash,
            series_checkpoint_hash=hash_value,
            series_entity_registry_hash=self.series_entity_registry_hash,
            manifest_fingerprint="",
        )

    def with_fingerprint(self, fingerprint: str) -> "SeriesManifest":
        return SeriesManifest(
            schema_name=self.schema_name,
            schema_version=self.schema_version,
            series_id=self.series_id,
            series_name=self.series_name,
            lifecycle_status=self.lifecycle_status,
            created_at=self.created_at,
            updated_at=self.updated_at,
            books=self.books,
            series_memory_hash=self.series_memory_hash,
            series_checkpoint_hash=self.series_checkpoint_hash,
            series_entity_registry_hash=self.series_entity_registry_hash,
            manifest_fingerprint=fingerprint,
        )

    def with_series_entity_registry_hash(self, hash_value: str) -> "SeriesManifest":
        return SeriesManifest(
            schema_name=self.schema_name,
            schema_version=self.schema_version,
            series_id=self.series_id,
            series_name=self.series_name,
            lifecycle_status=self.lifecycle_status,
            created_at=self.created_at,
            updated_at=utc_now_iso(),
            books=self.books,
            series_memory_hash=self.series_memory_hash,
            series_checkpoint_hash=self.series_checkpoint_hash,
            series_entity_registry_hash=hash_value,
            manifest_fingerprint="",
        )