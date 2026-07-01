from __future__ import annotations

from typing import Any

from core.quality.semantic_qa import SemanticQA
from core.quality.semantic_repair import SemanticRepair
from core.quality.coverage_checker import CoverageChecker

from .plugin_base import PluginBase
from .plugin_context import PluginContext


class QualityPlugin(PluginBase):
    name = "quality"
    stage = "quality"
    priority = 10

    def setup(self, context: PluginContext) -> None:
        self.semantic_qa = SemanticQA(root=context.root)
        self.semantic_repair = SemanticRepair(root=context.root)
        self.coverage_checker = CoverageChecker(root=context.root)

    def run(self, payload: dict[str, Any], context: PluginContext) -> dict[str, Any]:
        result = dict(payload)

        source_text = result.get("source_text") or result.get("chunk_text", "")
        translation_text = result.get("translation_text", "")

        if not source_text:
            raise ValueError("QualityPlugin missing source_text/chunk_text")

        if not translation_text:
            raise ValueError("QualityPlugin missing translation_text")

        semantic_before = self.semantic_qa.check(source_text, translation_text)

        repaired = False
        repair_result = {}

        if semantic_before.get("issue_count", 0) > 0:
            repair_result = self.semantic_repair.repair(source_text, translation_text)

            if repair_result.get("changed"):
                translation_text = repair_result["translation"]
                repaired = True

        coverage = self.coverage_checker.check(source_text, translation_text)
        semantic_after = self.semantic_qa.check(source_text, translation_text)

        result["translation_text"] = translation_text
        result["semantic_before"] = semantic_before
        result["semantic_after"] = semantic_after
        result["coverage"] = coverage
        result["semantic_repaired"] = repaired
        result["semantic_repair_result"] = repair_result

        return result