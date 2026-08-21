"""P0 Stage 5 Batch 5.7 — Series Orchestration Workflow State Machine.

Multi-book workflow state management for series translation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, List, Tuple, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class BookWorkflowState:
    """Runtime state of a book within a series translation workflow."""
    volume_number: int
    book_identity: str
    status: str  # "pending" | "in_progress" | "completed" | "promoted" | "failed" | "archived"
    hydration_done: bool
    translation_started_at: str | None
    translation_completed_at: str | None
    promotion_completed_at: str | None
    current_chunk: int
    total_chunks: int
    last_error: str | None

    def to_dict(self) -> dict:
        return {
            "volume_number": self.volume_number,
            "book_identity": self.book_identity,
            "status": self.status,
            "hydration_done": self.hydration_done,
            "translation_started_at": self.translation_started_at,
            "translation_completed_at": self.translation_completed_at,
            "promotion_completed_at": self.promotion_completed_at,
            "current_chunk": self.current_chunk,
            "total_chunks": self.total_chunks,
            "last_error": self.last_error,
        }


@dataclass(frozen=True)
class SeriesWorkflowState:
    """Runtime state of an entire series translation workflow."""
    series_id: str
    series_name: str
    lifecycle_status: str  # "CREATED" | "ACTIVE" | "COMPLETED" | "ARCHIVED"
    books: Tuple[BookWorkflowState, ...]
    next_volume_number: int
    next_actions: List[str]  # e.g., ["translate:volume_2", "promote:volume_1"]

    def to_dict(self) -> dict:
        return {
            "series_id": self.series_id,
            "series_name": self.series_name,
            "lifecycle_status": self.lifecycle_status,
            "books": [b.to_dict() for b in self.books],
            "next_volume_number": self.next_volume_number,
            "next_actions": self.next_actions,
        }


@dataclass(frozen=True)
class SeriesCreateResult:
    series_id: str
    manifest: Any  # SeriesManifest
    manifest_path: Any  # Path


@dataclass(frozen=True)
class BookAddResult:
    volume_number: int
    book_identity: str
    book_entry: Any  # SeriesBookEntry
    manifest: Any  # SeriesManifest
    manifest_path: Any  # Path


@dataclass(frozen=True)
class TranslationReport:
    series_id: str
    book_identity: str
    volume_number: int
    status: str  # "success" | "failed" | "interrupted"
    chunks_translated: int
    total_chunks: int
    hydration_summary: Any | None  # HydrationReport from series_memory
    checkpoint_id: str | None
    error: str | None


@dataclass(frozen=True)
class PromotionReport:
    series_id: str
    book_identity: str
    volume_number: int
    promotion_results: Tuple[Any, ...]  # SeriesAddResult from series_memory + series_entity + glossary
    memory_promotion: Any  # Tuple[SeriesAddResult, ...] from series_memory.promote_from_book()
    entity_promotion: Any  # Tuple[AddResult, ...] from series_entity.promote_from_resolver()
    glossary_promotion: Any  # Tuple[GlossaryPromotionRecord, ...] from merge_into_series_glossary()
    series_memory_hash: str
    series_entity_registry_hash: str
    series_glossary_hash: str
    series_knowledge_hash: str
    series_checkpoint_hash: str


@dataclass(frozen=True)
class SeriesStatusReport:
    series_id: str
    series_name: str
    lifecycle_status: str
    workflow_state: SeriesWorkflowState
    manifest: Any  # SeriesManifest
    latest_checkpoint: Any | None  # SeriesCheckpoint