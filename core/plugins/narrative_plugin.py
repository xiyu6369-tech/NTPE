from __future__ import annotations

from typing import Any

from core.narrative.narrative_intelligence import NarrativeIntelligenceEngine

from .plugin_base import PluginBase
from .plugin_context import PluginContext


class NarrativePlugin(PluginBase):
    name = "narrative"
    stage = "narrative"
    priority = 10

    def setup(self, context: PluginContext) -> None:
        self.engine = NarrativeIntelligenceEngine(context.root)

    def run(self, payload: dict[str, Any], context: PluginContext) -> dict[str, Any]:
        result = dict(payload)

        source_text = result.get("source_text") or result.get("chunk_text", "")
        if not source_text:
            raise ValueError("NarrativePlugin missing source_text/chunk_text")

        analysis = self.engine.analyze(source_text)
        prompt_rules = self.engine.build_prompt_rules(analysis)

        result["narrative_analysis"] = analysis
        result["narrative_prompt_rules"] = prompt_rules

        return result