from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceReadResult:
    source_path: Path
    filename: str
    extension: str
    byte_size: int
    raw_bytes: bytes


@dataclass(frozen=True)
class EncodingDetectionResult:
    encoding: str
    confidence: str
    detection_method: str
    bom_present: bool
    candidates: tuple[str, ...]
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class DecodedSource:
    encoding: str
    text: str
    byte_size: int
    character_count: int
    bom_removed: bool
    content_hash: str
