# =====================================================
# NTPE 1.2 Professional
# Stage-16.2 Narrative Intelligence
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

from .narrative_result import NarrativeSegment


@dataclass
class NarrativeContext:
    """Runtime-safe container for chapter/chunk narrative material."""

    context_id: str = "runtime"
    segments: List[NarrativeSegment] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_segment(self, segment: NarrativeSegment) -> None:
        self.segments.append(segment)

    def extend(self, segments: Iterable[NarrativeSegment]) -> None:
        self.segments.extend(segments)

    def to_text(self) -> str:
        return "\n".join(segment.text for segment in self.segments if segment.text.strip())
