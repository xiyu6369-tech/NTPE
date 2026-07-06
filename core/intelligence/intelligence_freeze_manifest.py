# =====================================================
# NTPE 1.2 Professional
# Stage-16.8 Advanced Translation Intelligence Freeze
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass(frozen=True)
class IntelligenceFreezeManifest:
    """Frozen baseline manifest for Stage-16 Advanced Translation Intelligence."""

    stage: str = "Stage-16.8"
    name: str = "Advanced Translation Intelligence Freeze"
    version: str = "1.2-professional-stage16.8"
    frozen: bool = True
    frozen_modules: List[str] = field(default_factory=lambda: [
        "Context Intelligence Engine",
        "Narrative Intelligence",
        "Character Relationship Intelligence",
        "Semantic Consistency Engine",
        "Translation Memory Intelligence",
        "Adaptive Translation Strategy",
        "Intelligence Runtime Integration",
    ])
    compatibility_targets: List[str] = field(default_factory=lambda: [
        "Foundation v1.0 Frozen",
        "NTPE 1.1 LTS Frozen",
        "Stage-14 Provider Framework Frozen",
        "Stage-15 Translation Quality Engine Frozen",
        "Stage-16.1-16.7 Intelligence Layer",
    ])
    public_contracts: Dict[str, str] = field(default_factory=lambda: {
        "runtime": "IntelligenceRuntime.analyze / analyze_text",
        "bridge": "TranslationIntelligenceBridge.prepare / build_translation_hints",
        "result": "IntelligenceRuntimeResult.to_dict / selected_strategy",
        "events": "IntelligenceRuntimeEventBus emit/listener contract",
        "metrics": "engine_count, engines_executed, selected_strategy",
    })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "name": self.name,
            "version": self.version,
            "frozen": self.frozen,
            "frozen_modules": list(self.frozen_modules),
            "compatibility_targets": list(self.compatibility_targets),
            "public_contracts": dict(self.public_contracts),
        }
