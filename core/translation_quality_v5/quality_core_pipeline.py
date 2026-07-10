from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from .quality_baseline import TranslationQualityBaseline
from .completeness_guard import CompletenessGuard
from .terminology_guard import TerminologyConsistencyGuard
from .traditional_chinese_normalizer import TraditionalChineseNormalizer


class TranslationQualityCorePipeline:
    version = "TE-v5.0"
    stage = "5.0.5"

    def __init__(self) -> None:
        self.baseline = TranslationQualityBaseline()
        self.completeness = CompletenessGuard()
        self.terminology = TerminologyConsistencyGuard()
        self.normalizer = TraditionalChineseNormalizer()

    def run(
        self,
        source_text: Optional[str],
        translated_text: Optional[str],
        *,
        locked_terms: Optional[Mapping[str, str]] = None,
        forbidden_variants: Optional[Mapping[str, list[str]]] = None,
        config: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        normalization = self.normalizer.normalize(translated_text)
        normalized_text = normalization["normalized_text"]

        terminology = self.terminology.evaluate(
            source_text,
            normalized_text,
            locked_terms=locked_terms,
            forbidden_variants=forbidden_variants,
        )
        repaired_text = terminology["repaired_text"]

        baseline = self.baseline.evaluate(
            source_text,
            repaired_text,
            locked_terms=locked_terms,
            config=config,
        )
        completeness = self.completeness.evaluate(
            source_text,
            repaired_text,
            config=config,
        )

        accepted = (
            baseline["accepted"]
            and completeness["accepted"]
            and terminology["accepted"]
            and normalization["simplified_residue_count"] == 0
        )

        repair_actions = []
        for issue in baseline["issues"]:
            action = issue["repair_action"]
            if action not in repair_actions:
                repair_actions.append(action)
        if normalization["simplified_residue_count"]:
            repair_actions.append("full_traditional_chinese_conversion")
        if terminology["repair_replacements"]:
            repair_actions.append("apply_locked_terminology")

        return {
            "accepted": accepted,
            "status": "quality_pass" if accepted else "quality_fail",
            "stage": self.stage,
            "quality_score": baseline["score"],
            "normalized_text": repaired_text,
            "baseline_report": baseline,
            "completeness_result": completeness,
            "terminology_result": terminology,
            "normalization_result": {
                key: value for key, value in normalization.items()
                if key != "normalized_text"
            },
            "repair_required": not accepted,
            "repair_actions": repair_actions,
            "retry_required": completeness["retry_required"]
                or any(
                    issue["code"] in {
                        "hangul_residue", "duplicate_paragraph", "too_short",
                        "paragraph_omission_suspected",
                        "sentence_omission_suspected",
                    }
                    for issue in baseline["issues"]
                ),
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
            "accepted", "status", "stage", "quality_score",
            "normalized_text", "baseline_report",
            "completeness_result", "terminology_result",
            "normalization_result", "repair_required",
            "repair_actions", "retry_required",
            "source_text_retained", "translated_text_retained",
            "integration_status"
        }
        if not required.issubset(result):
            return False
        if result.get("stage") != self.stage:
            return False
        if not self.baseline.validate_report(result.get("baseline_report")):
            return False
        if not self.completeness.validate_result(
            result.get("completeness_result")
        ):
            return False
        if not self.terminology.validate_result(
            result.get("terminology_result")
        ):
            return False
        integration = result.get("integration_status", {})
        if any(integration.get(k) is not False for k in (
            "provider_called", "http_called", "api_key_accessed",
            "runtime_modified", "launcher_modified",
            "real_translation_executed"
        )):
            return False
        return True
