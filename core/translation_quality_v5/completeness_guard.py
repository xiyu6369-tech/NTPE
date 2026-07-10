from __future__ import annotations

import re
from typing import Any, Dict, Mapping, Optional

from .quality_baseline import TranslationQualityBaseline


class CompletenessGuard:
    version = "TE-v5.0"
    stage = "5.0.2"

    def __init__(self) -> None:
        self.baseline = TranslationQualityBaseline()

    def evaluate(
        self,
        source_text: Optional[str],
        translated_text: Optional[str],
        *,
        config: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        report = self.baseline.evaluate(
            source_text,
            translated_text,
            config=config,
        )
        blocking_codes = {
            "empty_output",
            "too_short",
            "too_long",
            "paragraph_omission_suspected",
            "sentence_omission_suspected",
            "duplicate_paragraph",
        }
        issues = [
            issue for issue in report["issues"]
            if issue["code"] in blocking_codes
        ]
        accepted = not issues
        return {
            "accepted": accepted,
            "status": "complete" if accepted else "incomplete",
            "stage": self.stage,
            "issues": issues,
            "metrics": {
                key: report["metrics"][key]
                for key in (
                    "source_chars",
                    "translated_chars",
                    "length_ratio",
                    "source_paragraph_count",
                    "translated_paragraph_count",
                    "source_sentence_count",
                    "translated_sentence_count",
                    "duplicate_paragraph_count",
                )
            },
            "retry_required": not accepted,
            "recommended_action": (
                "accept"
                if accepted
                else self._recommended_action(issues)
            ),
            "source_text_retained": False,
            "translated_text_retained": False,
        }

    def validate_result(self, result: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(result, Mapping):
            return False
        required = {
            "accepted", "status", "stage", "issues", "metrics",
            "retry_required", "recommended_action",
            "source_text_retained", "translated_text_retained"
        }
        if not required.issubset(result):
            return False
        if result.get("stage") != self.stage:
            return False
        if result.get("accepted") is True and result.get("retry_required") is True:
            return False
        if result.get("accepted") is False and not result.get("issues"):
            return False
        return (
            result.get("source_text_retained") is False
            and result.get("translated_text_retained") is False
        )

    @staticmethod
    def _recommended_action(issues: list[dict[str, Any]]) -> str:
        codes = {issue["code"] for issue in issues}
        if "empty_output" in codes:
            return "retranslate_original_chunk"
        if "too_short" in codes or "paragraph_omission_suspected" in codes:
            return "split_and_retranslate"
        if "duplicate_paragraph" in codes:
            return "retranslate_without_previous_output"
        return "inspect_and_retranslate"
