from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from .quality_core_pipeline import TranslationQualityCorePipeline
from .quality_repair_planner import QualityRepairPlanner
from .quality_retry_orchestrator import QualityRetryOrchestrator
from .quality_chunk_rebuild_planner import QualityChunkRebuildPlanner


class QualityRepairPipeline:
    version = "TE-v5.1"
    stage = "5.1.4"

    def __init__(self) -> None:
        self.quality = TranslationQualityCorePipeline()
        self.repair = QualityRepairPlanner()
        self.retry = QualityRetryOrchestrator()
        self.rebuild = QualityChunkRebuildPlanner()

    def run(
        self,
        source_text: Optional[str],
        translated_text: Optional[str],
        *,
        locked_terms: Optional[Mapping[str, str]] = None,
        forbidden_variants: Optional[Mapping[str, list[str]]] = None,
        runtime_state: Optional[Mapping[str, Any]] = None,
        config: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        quality_result = self.quality.run(
            source_text,
            translated_text,
            locked_terms=locked_terms,
            forbidden_variants=forbidden_variants,
            config=config,
        )
        repair_plan = self.repair.plan(quality_result)
        retry_result = self.retry.build_retry_decision(
            repair_plan, runtime_state, config
        )
        rebuild_result = self.rebuild.build(
            source_text, retry_result, repair_plan, config
        )

        if quality_result["accepted"]:
            final_status = "accepted"
        elif retry_result["retry"]:
            final_status = "retry_planned"
        else:
            final_status = "repair_required"

        return {
            "stage": self.stage,
            "status": final_status,
            "accepted": quality_result["accepted"],
            "quality_result": quality_result,
            "repair_plan": repair_plan,
            "retry_result": retry_result,
            "rebuild_result": rebuild_result,
            "normalized_text": quality_result["normalized_text"],
            "source_text_retained": False,
            "translated_text_retained": False,
            "integration_status": {
                "provider_called": False,
                "http_called": False,
                "api_key_accessed": False,
                "runtime_modified": False,
                "launcher_modified": False,
                "real_translation_executed": False,
            },
        }

    def validate_result(self, result: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(result, Mapping):
            return False
        required = {
            "stage", "status", "accepted", "quality_result",
            "repair_plan", "retry_result", "rebuild_result",
            "normalized_text", "source_text_retained",
            "translated_text_retained", "integration_status"
        }
        if not required.issubset(result):
            return False
        if result.get("stage") != self.stage:
            return False
        if not self.quality.validate_result(result.get("quality_result")):
            return False
        if not self.repair.validate_plan(result.get("repair_plan")):
            return False
        if not self.retry.validate_result(result.get("retry_result")):
            return False
        if not self.rebuild.validate_result(result.get("rebuild_result")):
            return False
        integration = result.get("integration_status", {})
        return all(integration.get(key) is False for key in (
            "provider_called", "http_called", "api_key_accessed",
            "runtime_modified", "launcher_modified",
            "real_translation_executed"
        ))
