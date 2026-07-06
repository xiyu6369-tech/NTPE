# =====================================================
# NTPE 1.2 Professional
# Stage-16.8 Advanced Translation Intelligence Freeze
# =====================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class IntelligenceRuntimeContract:
    """Public contract for the frozen Stage-16 intelligence runtime layer."""

    stage: str = "Stage-16.8"
    runtime_entrypoint: str = "core.intelligence.intelligence_runtime.IntelligenceRuntime"
    bridge_entrypoint: str = "core.translation.intelligence_bridge.TranslationIntelligenceBridge"
    result_schema: str = "core.intelligence.intelligence_runtime_result.IntelligenceRuntimeResult"
    context_schema: str = "core.intelligence.intelligence_runtime_context.IntelligenceRuntimeContext"
    compatibility_level: str = "backward-compatible"

    def required_engines(self) -> Tuple[str, ...]:
        return (
            "context",
            "narrative",
            "character",
            "semantic",
            "memory",
            "strategy",
        )

    def frozen_public_methods(self) -> Dict[str, Tuple[str, ...]]:
        return {
            "IntelligenceRuntime": ("analyze", "analyze_text"),
            "TranslationIntelligenceBridge": ("prepare", "build_translation_hints"),
            "IntelligenceRuntimeResult": ("to_dict", "selected_strategy"),
        }

    def to_dict(self) -> Dict[str, object]:
        return {
            "stage": self.stage,
            "runtime_entrypoint": self.runtime_entrypoint,
            "bridge_entrypoint": self.bridge_entrypoint,
            "result_schema": self.result_schema,
            "context_schema": self.context_schema,
            "compatibility_level": self.compatibility_level,
            "required_engines": list(self.required_engines()),
            "frozen_public_methods": {k: list(v) for k, v in self.frozen_public_methods().items()},
        }
