"""Stage-07.2 SDK Translation request objects."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .options import TranslationOptions


@dataclass
class TranslationRequest:
    """Stable SDK translation request.

    Exactly one of text, file_path, or segments may be supplied by callers. The
    API remains permissive and resolves them in that order for compatibility.
    """

    text: Optional[str] = None
    file_path: Optional[str] = None
    segments: List[str] = field(default_factory=list)
    options: TranslationOptions = field(default_factory=TranslationOptions)

    def resolve_segments(self) -> List[str]:
        if self.text is not None:
            return [str(self.text)]
        if self.file_path:
            return [Path(self.file_path).read_text(encoding="utf-8")]
        return [str(item) for item in self.segments]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "file_path": self.file_path,
            "segments": list(self.segments),
            "options": self.options.to_dict(),
        }

    @classmethod
    def for_text(cls, text: str, options: Optional[TranslationOptions] = None) -> "TranslationRequest":
        return cls(text=text, options=options or TranslationOptions())

    @classmethod
    def for_file(cls, file_path: str, options: Optional[TranslationOptions] = None) -> "TranslationRequest":
        return cls(file_path=file_path, options=options or TranslationOptions())

    @classmethod
    def for_batch(cls, segments: Iterable[str], options: Optional[TranslationOptions] = None) -> "TranslationRequest":
        return cls(segments=[str(item) for item in segments], options=options or TranslationOptions())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TranslationRequest":
        payload = dict(data)
        return cls(
            text=payload.get("text"),
            file_path=payload.get("file_path"),
            segments=[str(item) for item in payload.get("segments", []) or []],
            options=TranslationOptions.from_dict(payload.get("options", {}) or {}),
        )
