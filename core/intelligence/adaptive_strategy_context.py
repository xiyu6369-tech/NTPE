# =====================================================
# NTPE 1.2 Professional
# Stage-16.6 Adaptive Translation Strategy
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping


@dataclass(frozen=True)
class AdaptiveStrategyContext:
    source_text: str
    source_language: str = "auto"
    target_language: str = "zh-TW"
    content_type_hint: str | None = None
    context_signals: Mapping[str, Any] = field(default_factory=dict)
    narrative_signals: Mapping[str, Any] = field(default_factory=dict)
    character_signals: Mapping[str, Any] = field(default_factory=dict)
    semantic_signals: Mapping[str, Any] = field(default_factory=dict)
    memory_signals: Mapping[str, Any] = field(default_factory=dict)
    provider_capabilities: Mapping[str, Any] = field(default_factory=dict)
    quality_risks: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
