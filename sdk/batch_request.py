"""Stage-07.3 SDK Batch request objects."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .batch_models import BatchItem, BatchOptions


@dataclass
class BatchRequest:
    """Stable SDK batch request for multi-text and multi-file translation."""

    items: List[BatchItem] = field(default_factory=list)
    options: BatchOptions = field(default_factory=BatchOptions)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": [item.to_dict() for item in self.items],
            "options": self.options.to_dict(),
        }

    @classmethod
    def from_texts(cls, texts: Iterable[str], options: Optional[BatchOptions] = None) -> "BatchRequest":
        return cls(items=[BatchItem(item_id=f"text-{index}", text=str(text)) for index, text in enumerate(texts)], options=options or BatchOptions())

    @classmethod
    def from_files(cls, file_paths: Iterable[str], options: Optional[BatchOptions] = None) -> "BatchRequest":
        items = []
        for index, file_path in enumerate(file_paths):
            path = Path(file_path)
            items.append(BatchItem(item_id=path.stem or f"file-{index}", file_path=str(path)))
        return cls(items=items, options=options or BatchOptions())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchRequest":
        payload = dict(data or {})
        return cls(
            items=[BatchItem.from_dict(item) for item in payload.get("items", []) or []],
            options=BatchOptions.from_dict(payload.get("options", {}) or {}),
        )
