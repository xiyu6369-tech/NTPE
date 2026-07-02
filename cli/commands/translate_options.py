from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class TranslateOptions:
    input_path: Path
    output_path: Optional[Path] = None
    resume: bool = False
    provider: str = "mock"
    quality: str = "standard"
    dry_run: bool = False
    pattern: str = "*.txt"
    overwrite: bool = False
    suffix: str = "_zh"

    @classmethod
    def from_args(cls, args: object) -> "TranslateOptions":
        input_value = getattr(args, "input", None)
        if input_value is None:
            raise ValueError("translate input is required")
        output_value = getattr(args, "output", None)
        return cls(
            input_path=Path(input_value),
            output_path=Path(output_value) if output_value else None,
            resume=bool(getattr(args, "resume", False)),
            provider=str(getattr(args, "provider", "mock") or "mock"),
            quality=str(getattr(args, "quality", "standard") or "standard"),
            dry_run=bool(getattr(args, "dry_run", False)),
            pattern=str(getattr(args, "pattern", "*.txt") or "*.txt"),
            overwrite=bool(getattr(args, "overwrite", False)),
            suffix=str(getattr(args, "suffix", "_zh") or "_zh"),
        )
