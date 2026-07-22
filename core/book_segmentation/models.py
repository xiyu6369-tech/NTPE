from __future__ import annotations

from dataclasses import dataclass


FindingValue = str | int | float | bool | None


@dataclass(frozen=True)
class ChapterHeading:
    """An exact heading line and its 0-based, half-open source coordinates."""

    text: str
    normalized_label: str
    line_index: int
    character_start: int
    character_end: int
    pattern_code: str
    confidence: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if self.line_index < 0 or self.character_start < 0:
            raise ValueError("heading coordinates cannot be negative")
        if self.character_end < self.character_start:
            raise ValueError("heading character_end cannot precede character_start")


@dataclass(frozen=True)
class BookSection:
    """One lossless, contiguous source slice with half-open coordinates."""

    index: int
    section_type: str
    heading: ChapterHeading | None
    text: str
    character_start: int
    character_end: int
    line_start: int
    line_end: int
    character_count: int
    non_whitespace_character_count: int

    def __post_init__(self) -> None:
        if min(self.index, self.character_start, self.line_start) < 0:
            raise ValueError("section coordinates cannot be negative")
        if self.character_end < self.character_start or self.line_end < self.line_start:
            raise ValueError("section end cannot precede section start")
        if self.character_count != len(self.text):
            raise ValueError("character_count must equal len(text)")
        if self.character_end - self.character_start != self.character_count:
            raise ValueError("section offsets must match character_count")
        if self.non_whitespace_character_count != sum(
            not character.isspace() for character in self.text
        ):
            raise ValueError("non_whitespace_character_count is inconsistent")


@dataclass(frozen=True)
class SegmentationFinding:
    code: str
    severity: str
    message: str
    section_index: int | None = None
    observed_value: FindingValue = None


@dataclass(frozen=True)
class BookSegmentationResult:
    source_name: str
    source_content_fingerprint: str
    strategy: str
    sections: tuple[BookSection, ...]
    chapter_count: int
    front_matter_count: int
    unclassified_count: int
    character_count: int
    covered_character_count: int
    coverage_ratio: float
    status: str
    action: str
    findings: tuple[SegmentationFinding, ...]
    summary: str
    segmentation_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.sections, tuple) or not isinstance(self.findings, tuple):
            raise TypeError("sections and findings must be tuples")

    def reconstruct_text(self) -> str:
        """Reconstruct the exact decoded source without separators or normalization."""
        return "".join(section.text for section in self.sections)
