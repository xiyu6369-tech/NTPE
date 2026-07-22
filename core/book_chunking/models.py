from __future__ import annotations

import re
from dataclasses import dataclass


FindingValue = str | int | float | bool | None
FindingThreshold = str | int | float | None
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ChunkBoundary:
    source_character_start: int
    source_character_end: int
    section_index: int
    section_character_start: int
    section_character_end: int
    boundary_type: str

    def __post_init__(self) -> None:
        if min(
            self.source_character_start,
            self.source_character_end,
            self.section_index,
            self.section_character_start,
            self.section_character_end,
        ) < 0:
            raise ValueError("boundary coordinates cannot be negative")
        if self.source_character_end < self.source_character_start:
            raise ValueError("boundary end cannot precede start")
        if self.section_character_end < self.section_character_start:
            raise ValueError("section-relative boundary end cannot precede start")


@dataclass(frozen=True)
class TranslationChunk:
    index: int
    text: str
    source_character_start: int
    source_character_end: int
    first_section_index: int
    last_section_index: int
    section_indices: tuple[int, ...]
    starts_at_section_boundary: bool
    ends_at_section_boundary: bool
    character_count: int
    non_whitespace_character_count: int
    heading_text: str | None
    boundary_reason: str
    content_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.section_indices, tuple):
            raise TypeError("section_indices must be a tuple")
        if min(
            self.index,
            self.source_character_start,
            self.first_section_index,
            self.last_section_index,
        ) < 0:
            raise ValueError("chunk coordinates cannot be negative")
        if self.source_character_end < self.source_character_start:
            raise ValueError("chunk end cannot precede start")
        if not self.section_indices:
            raise ValueError("a non-empty chunk must reference at least one section")
        if self.first_section_index != self.section_indices[0]:
            raise ValueError("first_section_index does not match section_indices")
        if self.last_section_index != self.section_indices[-1]:
            raise ValueError("last_section_index does not match section_indices")
        if self.character_count != len(self.text):
            raise ValueError("character_count must equal len(text)")
        if self.source_character_end - self.source_character_start != len(self.text):
            raise ValueError("chunk offsets must match text length")
        if self.non_whitespace_character_count != sum(not char.isspace() for char in self.text):
            raise ValueError("non_whitespace_character_count is inconsistent")
        if not _HEX_64.fullmatch(self.content_fingerprint):
            raise ValueError("content_fingerprint must be lowercase SHA-256 hex")


@dataclass(frozen=True)
class ChunkPlanningFinding:
    code: str
    severity: str
    message: str
    chunk_index: int | None = None
    section_index: int | None = None
    observed_value: FindingValue = None
    threshold: FindingThreshold = None


@dataclass(frozen=True)
class BookChunkPlan:
    source_name: str
    source_content_fingerprint: str
    segmentation_fingerprint: str
    strategy: str
    target_chunk_size: int
    maximum_chunk_size: int
    minimum_chunk_size: int
    chunks: tuple[TranslationChunk, ...]
    chunk_count: int
    section_count: int
    character_count: int
    covered_character_count: int
    coverage_ratio: float
    status: str
    action: str
    findings: tuple[ChunkPlanningFinding, ...]
    summary: str
    chunk_plan_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.chunks, tuple) or not isinstance(self.findings, tuple):
            raise TypeError("chunks and findings must be tuples")
        if self.chunk_count != len(self.chunks):
            raise ValueError("chunk_count must equal len(chunks)")
        if not _HEX_64.fullmatch(self.chunk_plan_fingerprint):
            raise ValueError("chunk_plan_fingerprint must be lowercase SHA-256 hex")

    def reconstruct_text(self) -> str:
        return "".join(chunk.text for chunk in self.chunks)
