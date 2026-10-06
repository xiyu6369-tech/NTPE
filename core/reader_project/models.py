"""Reader Project schema v1 (S9-02).

Pure data models. No I/O, no runtime imports.

The Project schema is deliberately independent from runtime internal objects
(S9 §4): runtime state is referenced, never embedded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


SCHEMA_VERSION = 1


class ReaderStatus(str, Enum):
    """Reader-facing state model (S9 §8).

    Values are stable identifiers; display strings are owned by the UI layer.
    Runtime internal statuses must be mapped onto these, never displayed raw.
    """

    NOT_STARTED = "not_started"
    TRANSLATING = "translating"
    RESUMABLE = "resumable"
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"
    FAILED = "failed"
    SOURCE_CHANGED = "source_changed"
    UNRECOVERABLE = "unrecoverable"


VALID_FORMATS = ("txt", "epub")


def _clean_str(value: Any, default: str = "") -> str:
    return str(value) if value is not None else default


def _clean_opt_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _clean_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _clean_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@dataclass
class SourceRecord:
    path: str
    format: str = "txt"
    identity_kind: str = "txt_sha256_16"
    hash: str = ""
    file_size: int = 0
    modified_time: float = 0.0
    title: str = ""
    language: str = "ko"
    encoding: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "format": self.format,
            "identity_kind": self.identity_kind,
            "hash": self.hash,
            "file_size": self.file_size,
            "modified_time": self.modified_time,
            "title": self.title,
            "language": self.language,
            "encoding": self.encoding,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SourceRecord":
        return cls(
            path=_clean_str(data.get("path")),
            format=_clean_str(data.get("format"), "txt"),
            identity_kind=_clean_str(data.get("identity_kind"), "txt_sha256_16"),
            hash=_clean_str(data.get("hash")),
            file_size=_clean_int(data.get("file_size")),
            modified_time=_clean_float(data.get("modified_time")),
            title=_clean_str(data.get("title")),
            language=_clean_str(data.get("language"), "ko"),
            encoding=_clean_opt_str(data.get("encoding")),
        )


@dataclass
class BookRecord:
    format: str = "txt"
    title: str = ""
    author: str | None = None
    identifier: str | None = None
    chapter_count: int | None = None
    total_units: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": self.format,
            "title": self.title,
            "author": self.author,
            "identifier": self.identifier,
            "chapter_count": self.chapter_count,
            "total_units": self.total_units,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BookRecord":
        chapter_count = data.get("chapter_count")
        total_units = data.get("total_units")
        return cls(
            format=_clean_str(data.get("format"), "txt"),
            title=_clean_str(data.get("title")),
            author=_clean_opt_str(data.get("author")),
            identifier=_clean_opt_str(data.get("identifier")),
            chapter_count=None if chapter_count is None else _clean_int(chapter_count),
            total_units=None if total_units is None else _clean_int(total_units),
        )


@dataclass
class TargetRecord:
    target_language: str = "zh-TW"
    quality_profile: str = "literary"

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_language": self.target_language,
            "quality_profile": self.quality_profile,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TargetRecord":
        return cls(
            target_language=_clean_str(data.get("target_language"), "zh-TW"),
            quality_profile=_clean_str(data.get("quality_profile"), "literary"),
        )


@dataclass
class StateRecord:
    reader_status: str = ReaderStatus.NOT_STARTED.value
    completed_units: int = 0
    total_units: int = 0
    current_unit: int | None = None
    last_error: str | None = None
    recovery_eligible: bool = False
    recovery_blocked_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "reader_status": self.reader_status,
            "completed_units": self.completed_units,
            "total_units": self.total_units,
            "current_unit": self.current_unit,
            "last_error": self.last_error,
            "recovery_eligible": self.recovery_eligible,
            "recovery_blocked_reason": self.recovery_blocked_reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StateRecord":
        current_unit = data.get("current_unit")
        return cls(
            reader_status=_clean_str(data.get("reader_status"), ReaderStatus.NOT_STARTED.value),
            completed_units=_clean_int(data.get("completed_units")),
            total_units=_clean_int(data.get("total_units")),
            current_unit=None if current_unit is None else _clean_int(current_unit),
            last_error=_clean_opt_str(data.get("last_error")),
            recovery_eligible=bool(data.get("recovery_eligible", False)),
            recovery_blocked_reason=_clean_opt_str(data.get("recovery_blocked_reason", "")) or "",
        )


@dataclass
class ExecutionRecord:
    pipeline_mode: str = "runtime"
    session_id: str | None = None
    resume_state_path: str | None = None
    checkpoint_ref: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "pipeline_mode": self.pipeline_mode,
            "session_id": self.session_id,
            "resume_state_path": self.resume_state_path,
            "checkpoint_ref": self.checkpoint_ref,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionRecord":
        ref = data.get("checkpoint_ref")
        return cls(
            pipeline_mode=_clean_str(data.get("pipeline_mode"), "runtime"),
            session_id=_clean_opt_str(data.get("session_id")),
            resume_state_path=_clean_opt_str(data.get("resume_state_path")),
            checkpoint_ref=dict(ref) if isinstance(ref, dict) else None,
        )


@dataclass
class OutputRecord:
    output_dir: str | None = None
    artifact_path: str | None = None
    artifact_kind: str | None = None
    available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "output_dir": self.output_dir,
            "artifact_path": self.artifact_path,
            "artifact_kind": self.artifact_kind,
            "available": self.available,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OutputRecord":
        artifact_kind = _clean_opt_str(data.get("artifact_kind"))
        if artifact_kind is not None and artifact_kind not in VALID_FORMATS:
            artifact_kind = None
        return cls(
            output_dir=_clean_opt_str(data.get("output_dir")),
            artifact_path=_clean_opt_str(data.get("artifact_path")),
            artifact_kind=artifact_kind,
            available=bool(data.get("available", False)),
        )


@dataclass
class GlossaryRecord:
    """Project-scoped Glossary attachment (S12-02, schema v1 additive extension).

    ``stored_path`` points at the project-owned atomic snapshot; ``entries`` /
    ``aliases`` carry the normalized content so the record is self-describing.
    """

    mode: str = "none"  # "none" | "project_file"
    glossary_id: str = ""
    content_hash: str = ""
    format: str = ""
    original_path: str = ""
    stored_path: str = ""
    term_count: int = 0
    entries: dict[str, str] = field(default_factory=dict)
    aliases: dict[str, str] = field(default_factory=dict)
    imported_at: str = ""
    source_hash_at_import: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "glossary_id": self.glossary_id,
            "content_hash": self.content_hash,
            "format": self.format,
            "original_path": self.original_path,
            "stored_path": self.stored_path,
            "term_count": self.term_count,
            "entries": dict(self.entries),
            "aliases": dict(self.aliases),
            "imported_at": self.imported_at,
            "source_hash_at_import": self.source_hash_at_import,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GlossaryRecord":
        entries = data.get("entries")
        aliases = data.get("aliases")
        return cls(
            mode=_clean_str(data.get("mode"), "none"),
            glossary_id=_clean_str(data.get("glossary_id")),
            content_hash=_clean_str(data.get("content_hash")),
            format=_clean_str(data.get("format")),
            original_path=_clean_str(data.get("original_path")),
            stored_path=_clean_str(data.get("stored_path")),
            term_count=_clean_int(data.get("term_count")),
            entries=dict(entries) if isinstance(entries, dict) else {},
            aliases=dict(aliases) if isinstance(aliases, dict) else {},
            imported_at=_clean_str(data.get("imported_at")),
            source_hash_at_import=_clean_opt_str(data.get("source_hash_at_import")),
        )


@dataclass
class ReaderProject:
    """The persistent reader-facing project unit."""

    project_id: str
    source: SourceRecord
    book: BookRecord = field(default_factory=BookRecord)
    target: TargetRecord = field(default_factory=TargetRecord)
    state: StateRecord = field(default_factory=StateRecord)
    execution: ExecutionRecord = field(default_factory=ExecutionRecord)
    output: OutputRecord = field(default_factory=OutputRecord)
    glossary: GlossaryRecord | None = None
    project_schema_version: int = SCHEMA_VERSION
    created_at: str = ""
    updated_at: str = ""
    last_activity_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_schema_version": self.project_schema_version,
            "project_id": self.project_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_activity_at": self.last_activity_at,
            "source": self.source.to_dict(),
            "target": self.target.to_dict(),
            "book": self.book.to_dict(),
            "state": self.state.to_dict(),
            "execution": self.execution.to_dict(),
            "output": self.output.to_dict(),
            "glossary": self.glossary.to_dict() if self.glossary is not None else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReaderProject":
        glossary = data.get("glossary")
        return cls(
            project_id=_clean_str(data.get("project_id")),
            source=SourceRecord.from_dict(data.get("source") or {}),
            target=TargetRecord.from_dict(data.get("target") or {}),
            book=BookRecord.from_dict(data.get("book") or {}),
            state=StateRecord.from_dict(data.get("state") or {}),
            execution=ExecutionRecord.from_dict(data.get("execution") or {}),
            output=OutputRecord.from_dict(data.get("output") or {}),
            glossary=GlossaryRecord.from_dict(glossary) if isinstance(glossary, dict) else None,
            project_schema_version=_clean_int(
                data.get("project_schema_version"), SCHEMA_VERSION
            ),
            created_at=_clean_str(data.get("created_at")),
            updated_at=_clean_str(data.get("updated_at")),
            last_activity_at=_clean_str(data.get("last_activity_at")),
        )
