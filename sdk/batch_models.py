"""Stage-07.3 SDK Batch model objects.

Additive SDK models for multi-file batch translation. These objects do not
change Foundation, Runtime, Translation, Provider, Quality, CLI, or Stage-07.2
Translation API contracts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .options import TranslationOptions


@dataclass
class BatchItem:
    """Single input item for SDK batch translation."""

    item_id: str
    text: Optional[str] = None
    file_path: Optional[str] = None
    output_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def resolve_text(self) -> str:
        if self.text is not None:
            return str(self.text)
        if self.file_path:
            return Path(self.file_path).read_text(encoding="utf-8")
        return ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "text": self.text,
            "file_path": self.file_path,
            "output_path": self.output_path,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchItem":
        payload = dict(data)
        return cls(
            item_id=str(payload.get("item_id") or payload.get("id") or "batch-item"),
            text=payload.get("text"),
            file_path=payload.get("file_path"),
            output_path=payload.get("output_path"),
            metadata=dict(payload.get("metadata", {}) or {}),
        )


@dataclass
class BatchProgress:
    """Serializable progress snapshot for SDK batch execution."""

    total: int = 0
    completed: int = 0
    failed: int = 0
    current_item_id: Optional[str] = None

    @property
    def percent(self) -> float:
        if self.total <= 0:
            return 0.0
        return round(((self.completed + self.failed) / self.total) * 100, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "current_item_id": self.current_item_id,
            "percent": self.percent,
        }


@dataclass
class BatchResult:
    """Per-item SDK batch result."""

    item_id: str
    ok: bool
    text: str = ""
    output_path: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "ok": self.ok,
            "text": self.text,
            "output_path": self.output_path,
            "errors": list(self.errors),
            "data": dict(self.data),
        }

    @classmethod
    def success(cls, item_id: str, text: str, *, output_path: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> "BatchResult":
        return cls(item_id=item_id, ok=True, text=text, output_path=output_path, data=dict(data or {}))

    @classmethod
    def failure(cls, item_id: str, message: str, *, data: Optional[Dict[str, Any]] = None) -> "BatchResult":
        return cls(item_id=item_id, ok=False, errors=[str(message)], data=dict(data or {}))


@dataclass
class BatchOptions:
    """Batch-level execution options.

    The embedded TranslationOptions object keeps Stage-07.2 behavior available
    while adding batch-specific controls.
    """

    job_id: str = "sdk-batch-job"
    continue_on_error: bool = True
    write_outputs: bool = False
    output_dir: Optional[str] = None
    translation_options: TranslationOptions = field(default_factory=TranslationOptions)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def merged_translation_options(self, item: BatchItem, index: int) -> TranslationOptions:
        opts = TranslationOptions.from_dict(self.translation_options.to_dict())
        opts.job_id = self.job_id
        merged = dict(opts.metadata)
        merged.update(dict(self.metadata))
        merged.update(dict(item.metadata))
        merged.setdefault("batch_item_id", item.item_id)
        merged.setdefault("batch_item_index", index)
        opts.metadata = merged
        return opts

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "continue_on_error": self.continue_on_error,
            "write_outputs": self.write_outputs,
            "output_dir": self.output_dir,
            "translation_options": self.translation_options.to_dict(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchOptions":
        payload = dict(data or {})
        return cls(
            job_id=str(payload.get("job_id", "sdk-batch-job")),
            continue_on_error=bool(payload.get("continue_on_error", True)),
            write_outputs=bool(payload.get("write_outputs", False)),
            output_dir=payload.get("output_dir"),
            translation_options=TranslationOptions.from_dict(payload.get("translation_options", {}) or {}),
            metadata=dict(payload.get("metadata", {}) or {}),
        )
