"""RM-6.2.0 Prompt Runtime builder.

Assembles structured prompt sections from MergedRuntime.
Does NOT generate actual prompts — only assembles sections in order.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.knowledge_runtime.merger import MergedRuntime
from core.prompt_runtime.models import (
    SECTION_ORDER,
    SECTION_MAP,
    ChunkSection,
    PromptSection,
    SystemSection,
)
from core.prompt_runtime.sections import (
    SECTION_BUILDERS,
    build_chunk,
    build_system,
)


@dataclass(frozen=True)
class PromptAssembly:
    """Result of prompt assembly — ordered sections ready for consumption."""

    sections: List[PromptSection] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "rm-6.2.0"

    @property
    def section_count(self) -> int:
        return len(self.sections)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sections": [s.to_dict() for s in self.sections],
            "metadata": dict(self.metadata),
            "version": self.version,
            "section_count": self.section_count,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "PromptAssembly":
        sections = [SECTION_MAP[s["name"]].from_dict(s) for s in payload.get("sections", [])]
        return cls(
            sections=sections,
            metadata=dict(payload.get("metadata") or {}),
            version=str(payload.get("version", "rm-6.2.0")),
        )


class PromptBuilder:
    """Builds PromptAssembly from MergedRuntime.

    Section order (fixed):
        System → Character → Glossary → Scene → Narrative → Style → Chunk
    """

    def __init__(self, chunk_text: str = "", system_metadata: Optional[Dict[str, Any]] = None):
        self._chunk_text = chunk_text
        self._system_metadata = system_metadata or {}

    def build(self, runtime: MergedRuntime) -> PromptAssembly:
        """Assemble all sections in fixed order from runtime."""
        sections: List[PromptSection] = []

        # System (always first)
        sections.append(build_system(runtime, self._system_metadata))

        # Domain sections (fixed order)
        for section_name in SECTION_ORDER[1:-1]:  # Skip System and Chunk
            builder = SECTION_BUILDERS[section_name]
            sections.append(builder(runtime))

        # Chunk (always last)
        sections.append(build_chunk(runtime, self._chunk_text))

        return PromptAssembly(
            sections=sections,
            metadata={
                "runtime_version": runtime.version,
                "runtime_domains": list(runtime.domains.keys()),
                "chunk_text_length": len(self._chunk_text),
            },
            version="rm-6.2.0",
        )

    def build_partial(
        self,
        runtime: MergedRuntime,
        include: Optional[List[str]] = None,
    ) -> PromptAssembly:
        """Build only specified sections (for testing/debugging)."""
        if include is None:
            include = list(SECTION_ORDER)

        sections: List[PromptSection] = []
        for section_name in SECTION_ORDER:
            if section_name not in include:
                continue
            if section_name == "System":
                sections.append(build_system(runtime, self._system_metadata))
            elif section_name == "Chunk":
                sections.append(build_chunk(runtime, self._chunk_text))
            else:
                builder = SECTION_BUILDERS[section_name]
                sections.append(builder(runtime))

        return PromptAssembly(
            sections=sections,
            metadata={
                "runtime_version": runtime.version,
                "included_sections": include,
            },
            version="rm-6.2.0",
        )


def build_prompt(runtime: MergedRuntime, chunk_text: str = "") -> PromptAssembly:
    """Convenience function to build full prompt assembly.

    Args:
        runtime: MergedRuntime from knowledge_runtime
        chunk_text: Source text chunk to translate

    Returns:
        PromptAssembly with all sections in fixed order
    """
    builder = PromptBuilder(chunk_text=chunk_text)
    return builder.build(runtime)


__all__ = [
    "PromptAssembly",
    "PromptBuilder",
    "build_prompt",
]