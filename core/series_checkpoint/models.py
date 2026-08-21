"""P0 Stage 5 Batch 5.6 — Series Checkpoint Models.

Immutable dataclasses for Series-level checkpoint hierarchy with
full integrity verification.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from core.runtime_checkpoint.models import ProgressState, RequestManifest


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def to_canonical_json(obj: dict) -> str:
    """Deterministic JSON: sorted keys, no whitespace, UTF-8."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _generate_checkpoint_id(series_id: str) -> str:
    """Generate deterministic checkpoint ID: scheck_{sha256(series_id|timestamp)[:12]}"""
    timestamp = utc_now_iso()
    return f"scheck_{hashlib.sha256(f'{series_id}|{timestamp}'.encode()).hexdigest()[:12]}"


@dataclass(frozen=True)
class BookCheckpointRef:
    """Reference to a book's checkpoint state within Series."""
    book_identity: str
    volume_number: int
    book_memory_hash: str
    book_context_hash: str
    latest_session_checkpoint_id: str | None
    status: str  # "in_progress" | "completed" | "promoted"

    def to_dict(self) -> dict[str, Any]:
        return {
            "book_identity": self.book_identity,
            "volume_number": self.volume_number,
            "book_memory_hash": self.book_memory_hash,
            "book_context_hash": self.book_context_hash,
            "latest_session_checkpoint_id": self.latest_session_checkpoint_id,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BookCheckpointRef":
        return cls(
            book_identity=str(data["book_identity"]),
            volume_number=int(data["volume_number"]),
            book_memory_hash=str(data["book_memory_hash"]),
            book_context_hash=str(data["book_context_hash"]),
            latest_session_checkpoint_id=data.get("latest_session_checkpoint_id"),
            status=str(data["status"]),
        )


@dataclass(frozen=True)
class SessionCheckpointRef:
    """Reference to a session's checkpoint within a Book."""
    session_id: str
    chunk_index: int
    progress: ProgressState
    context_memory_hash: str
    request_manifest: RequestManifest | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "chunk_index": self.chunk_index,
            "progress": {
                "current_chunk": self.progress.current_chunk,
                "completed_chunks": self.progress.completed_chunks,
                "total_chunks": self.progress.total_chunks,
                "status": self.progress.status.value,
            },
            "context_memory_hash": self.context_memory_hash,
            "request_manifest": (
                {
                    "request_hash": self.request_manifest.request_hash,
                    "prompt_hash": self.request_manifest.prompt_hash,
                    "snapshot_id": self.request_manifest.snapshot_id,
                    "chunk_index": self.request_manifest.chunk_index,
                }
                if self.request_manifest
                else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionCheckpointRef":
        from core.runtime_checkpoint.models import ProgressStatus
        progress_data = data.get("progress", {})
        progress = ProgressState(
            current_chunk=progress_data.get("current_chunk", 0),
            completed_chunks=progress_data.get("completed_chunks", 0),
            total_chunks=progress_data.get("total_chunks", 0),
            status=ProgressStatus(progress_data.get("status", "ACTIVE")),
        )
        rm_data = data.get("request_manifest")
        request_manifest = None
        if rm_data:
            request_manifest = RequestManifest(
                request_hash=rm_data["request_hash"],
                prompt_hash=rm_data["prompt_hash"],
                snapshot_id=rm_data["snapshot_id"],
                chunk_index=rm_data["chunk_index"],
            )
        return cls(
            session_id=str(data["session_id"]),
            chunk_index=int(data["chunk_index"]),
            progress=progress,
            context_memory_hash=str(data["context_memory_hash"]),
            request_manifest=request_manifest,
        )


@dataclass(frozen=True)
class SeriesCheckpoint:
    """Series-level recovery checkpoint with full hierarchy integrity."""
    schema_name: str = "ntpe.series_checkpoint"
    schema_version: str = "1.0"
    series_id: str = ""
    checkpoint_id: str = ""
    created_at: str = ""
    series_memory_hash: str = ""
    series_entity_registry_hash: str = ""
    series_glossary_hash: str = ""
    series_knowledge_hash: str = ""
    manifest_fingerprint: str = ""
    book_checkpoints: tuple[BookCheckpointRef, ...] = field(default_factory=tuple)
    state_hash: str = ""

    def to_dict(self, include_state_hash: bool = True) -> dict[str, Any]:
        payload = {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "series_id": self.series_id,
            "checkpoint_id": self.checkpoint_id,
            "created_at": self.created_at,
            "series_memory_hash": self.series_memory_hash,
            "series_entity_registry_hash": self.series_entity_registry_hash,
            "series_glossary_hash": self.series_glossary_hash,
            "series_knowledge_hash": self.series_knowledge_hash,
            "manifest_fingerprint": self.manifest_fingerprint,
            "book_checkpoints": [b.to_dict() for b in self.book_checkpoints],
        }
        if include_state_hash:
            payload["state_hash"] = self.state_hash
        return payload

    def to_canonical_dict(self) -> dict[str, Any]:
        """Return canonical dict for fingerprint computation (excludes state_hash)."""
        return self.to_dict(include_state_hash=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SeriesCheckpoint":
        book_checkpoints = tuple(BookCheckpointRef.from_dict(b) for b in data.get("book_checkpoints", []))
        return cls(
            schema_name=data.get("schema_name", "ntpe.series_checkpoint"),
            schema_version=data.get("schema_version", "1.0"),
            series_id=str(data["series_id"]),
            checkpoint_id=str(data["checkpoint_id"]),
            created_at=str(data["created_at"]),
            series_memory_hash=str(data.get("series_memory_hash", "")),
            series_entity_registry_hash=str(data.get("series_entity_registry_hash", "")),
            series_glossary_hash=str(data.get("series_glossary_hash", "")),
            series_knowledge_hash=str(data.get("series_knowledge_hash", "")),
            manifest_fingerprint=str(data.get("manifest_fingerprint", "")),
            book_checkpoints=book_checkpoints,
            state_hash=str(data.get("state_hash", "")),
        )

    def get_checkpoint_hash(self) -> str:
        """Return state_hash for manifest integration."""
        return self.state_hash

    def with_hash(self) -> "SeriesCheckpoint":
        """Return new SeriesCheckpoint with computed state_hash."""
        fingerprint = compute_series_checkpoint_fingerprint(self.to_canonical_dict())
        return SeriesCheckpoint(
            schema_name=self.schema_name,
            schema_version=self.schema_version,
            series_id=self.series_id,
            checkpoint_id=self.checkpoint_id,
            created_at=self.created_at,
            series_memory_hash=self.series_memory_hash,
            series_entity_registry_hash=self.series_entity_registry_hash,
            series_glossary_hash=self.series_glossary_hash,
            series_knowledge_hash=self.series_knowledge_hash,
            manifest_fingerprint=self.manifest_fingerprint,
            book_checkpoints=self.book_checkpoints,
            state_hash=fingerprint,
        )


@dataclass(frozen=True)
class CheckpointCreationReport:
    series_id: str
    checkpoint_id: str
    created_at: str
    state_hash: str
    book_checkpoints_count: int
    session_checkpoints_total: int
    manifest_fingerprint: str


@dataclass(frozen=True)
class BookResumeInfo:
    volume_number: int
    book_identity: str
    book_status: str
    latest_session_id: str | None
    next_chunk_index: int
    hydration_required: bool


@dataclass(frozen=True)
class SeriesResumeReport:
    series_id: str
    series_checkpoint_id: str
    series_manifest: Any  # SeriesManifest - avoid circular import
    books_to_resume: list[BookResumeInfo]
    next_actions: list[str]


@dataclass(frozen=True)
class BookResumeReport:
    series_id: str
    book_identity: str
    volume_number: int
    book_memory_hash: str
    book_context_hash: str
    session_checkpoint: SessionCheckpointRef | None
    next_chunk_index: int
    hydration_summary: Any | None  # HydrationReport from series_memory


@dataclass(frozen=True)
class BookStartReport:
    series_id: str
    book_identity: str
    volume_number: int
    book_manifest: Any  # BookIntakeManifest - avoid circular import
    hydration_summary: Any  # HydrationReport from series_memory
    book_checkpoint_ref: BookCheckpointRef


def compute_series_checkpoint_fingerprint(series_checkpoint_dict: dict) -> str:
    """Compute SHA-256 of canonical checkpoint payload (excluding state_hash itself)."""
    payload = {k: v for k, v in series_checkpoint_dict.items() if k != "state_hash"}
    canonical = to_canonical_json(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()