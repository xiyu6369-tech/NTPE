# =====================================================
# NTPE 1.2 Professional
# Stage-16.7 Intelligence Runtime Integration
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Sequence


@dataclass(frozen=True)
class IntelligenceRuntimeContext:
    """Immutable input contract for the Stage-16 intelligence runtime."""

    source_text: str
    previous_texts: Sequence[str] = field(default_factory=list)
    source_language: str = "auto"
    target_language: str = "zh-TW"
    context_id: str = "runtime"
    metadata: Mapping[str, Any] = field(default_factory=dict)
    terminology: Mapping[str, str] = field(default_factory=dict)
    character_refs: Sequence[str] = field(default_factory=list)
    provider_capabilities: Mapping[str, Any] = field(default_factory=dict)
    quality_risks: List[str] = field(default_factory=list)

    def all_texts(self) -> List[str]:
        return [text for text in [*self.previous_texts, self.source_text] if text and text.strip()]

    def to_strategy_signals(self) -> Dict[str, Any]:
        return {
            "source_language": self.source_language,
            "target_language": self.target_language,
            "context_id": self.context_id,
            "metadata": dict(self.metadata),
        }
