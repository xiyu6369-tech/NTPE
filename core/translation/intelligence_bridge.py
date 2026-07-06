# =====================================================
# NTPE 1.2 Professional
# Stage-16.7 Intelligence Runtime Integration
# =====================================================

from __future__ import annotations

from typing import Any, Dict, Sequence

from core.intelligence.intelligence_runtime import IntelligenceRuntime
from core.intelligence.intelligence_runtime_context import IntelligenceRuntimeContext
from core.intelligence.intelligence_runtime_result import IntelligenceRuntimeResult


class TranslationIntelligenceBridge:
    """Small adapter for binding IntelligenceRuntime into translation runtime code paths."""

    def __init__(self, runtime: IntelligenceRuntime | None = None) -> None:
        self.runtime = runtime or IntelligenceRuntime()

    def prepare(self, source_text: str, *, previous_texts: Sequence[str] | None = None, **metadata: Any) -> IntelligenceRuntimeResult:
        context = IntelligenceRuntimeContext(
            source_text=source_text,
            previous_texts=previous_texts or [],
            source_language=str(metadata.get("source_language", "auto")),
            target_language=str(metadata.get("target_language", "zh-TW")),
            context_id=str(metadata.get("context_id", "translation_runtime")),
            metadata=dict(metadata.get("metadata", {})),
            terminology=dict(metadata.get("terminology", {})),
            character_refs=list(metadata.get("character_refs", [])),
            provider_capabilities=dict(metadata.get("provider_capabilities", {})),
            quality_risks=list(metadata.get("quality_risks", [])),
        )
        return self.runtime.analyze(context)

    def build_translation_hints(self, result: IntelligenceRuntimeResult) -> Dict[str, Any]:
        return {
            "stage": result.stage,
            "selected_strategy": result.selected_strategy,
            "metrics": dict(result.metrics),
            "intelligence": result.to_dict(),
        }
