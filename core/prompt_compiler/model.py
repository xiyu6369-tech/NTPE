from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class PromptSections:
    """Structured prompt inputs compiled into provider-ready text."""

    system: str
    policy: str
    context: str
    glossary: str
    source: str
    output: str
    optional: tuple[str, ...] = ()

    def ordered_user_sections(self) -> tuple[str, ...]:
        return (self.policy, self.context, self.glossary, *self.optional, self.source, self.output)


@dataclass(frozen=True)
class CompiledPrompt:
    system_prompt: str
    user_prompt: str
    compiler_version: str
    section_order: tuple[str, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "version": self.compiler_version,
            "section_order": list(self.section_order),
            **dict(self.metadata),
        }
