from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RuntimeContext:
    previous_summary: str = ""
    previous_chunk_tail: str = ""
    recent_characters: list[str] = field(default_factory=list)
    recent_terms: list[str] = field(default_factory=list)

    def to_package_context(self) -> dict:
        return {
            "previous_summary": self.previous_summary,
            "previous_chunk_tail": self.previous_chunk_tail,
            "recent_characters": list(self.recent_characters),
            "recent_terms": list(self.recent_terms),
        }
