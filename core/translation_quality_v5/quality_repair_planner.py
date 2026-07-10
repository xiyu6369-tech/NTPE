from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional


class QualityRepairPlanner:
    version = "TE-v5.1"
    stage = "5.1.1"

    _ACTION_MAP = {
        "empty_output": ("retranslate_original_chunk", "critical"),
        "too_short": ("split_and_retranslate", "critical"),
        "too_long": ("retranslate_without_previous_output", "high"),
        "hangul_residue": ("retranslate_residual_or_split", "critical"),
        "duplicate_paragraph": ("retranslate_without_previous_output", "high"),
        "duplicate_line": ("deduplicate_or_retranslate", "medium"),
        "paragraph_omission_suspected": ("split_and_retranslate", "high"),
        "sentence_omission_suspected": ("split_and_retranslate", "high"),
        "locked_term_missing": ("apply_locked_terminology", "high"),
        "dialogue_quote_format": ("normalize_dialogue_quotes", "low"),
    }

    def plan(
        self,
        quality_result: Optional[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        data = dict(quality_result or {})
        baseline = dict(data.get("baseline_report") or {})
        issues = list(baseline.get("issues") or [])
        normalization = dict(data.get("normalization_result") or {})
        terminology = dict(data.get("terminology_result") or {})

        actions: List[Dict[str, Any]] = []
        seen = set()
        retry_required = False
        split_required = False
        normalization_required = False
        terminology_repair_required = False

        for issue in issues:
            code = str(issue.get("code") or "unknown")
            action, severity = self._ACTION_MAP.get(
                code, ("inspect_and_retranslate", "medium")
            )
            key = (code, action)
            if key not in seen:
                actions.append({
                    "issue_code": code,
                    "action": action,
                    "severity": severity,
                })
                seen.add(key)
            if action in {
                "retranslate_original_chunk",
                "split_and_retranslate",
                "retranslate_without_previous_output",
                "retranslate_residual_or_split",
                "deduplicate_or_retranslate",
                "inspect_and_retranslate",
            }:
                retry_required = True
            if action in {"split_and_retranslate", "retranslate_residual_or_split"}:
                split_required = True
            if action == "normalize_dialogue_quotes":
                normalization_required = True
            if action == "apply_locked_terminology":
                terminology_repair_required = True

        if int(normalization.get("simplified_residue_count", 0) or 0) > 0:
            normalization_required = True
            if ("simplified_chinese_residue", "full_traditional_chinese_conversion") not in seen:
                actions.append({
                    "issue_code": "simplified_chinese_residue",
                    "action": "full_traditional_chinese_conversion",
                    "severity": "high",
                })

        if terminology.get("repair_replacements"):
            terminology_repair_required = True

        if data.get("accepted") is True and not actions:
            decision = "accept"
        elif retry_required:
            decision = "retry"
        else:
            decision = "repair_only"

        return {
            "stage": self.stage,
            "decision": decision,
            "quality_accepted": data.get("accepted") is True,
            "retry_required": retry_required,
            "split_required": split_required,
            "normalization_required": normalization_required,
            "terminology_repair_required": terminology_repair_required,
            "actions": actions,
            "priority": self._priority(actions),
            "source_text_retained": False,
            "translated_text_retained": False,
        }

    def validate_plan(self, plan: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(plan, Mapping):
            return False
        required = {
            "stage", "decision", "quality_accepted", "retry_required",
            "split_required", "normalization_required",
            "terminology_repair_required", "actions", "priority",
            "source_text_retained", "translated_text_retained"
        }
        if not required.issubset(plan):
            return False
        if plan.get("stage") != self.stage:
            return False
        if plan.get("decision") not in {"accept", "repair_only", "retry"}:
            return False
        if plan.get("source_text_retained") is not False:
            return False
        if plan.get("translated_text_retained") is not False:
            return False
        return isinstance(plan.get("actions"), list)

    @staticmethod
    def _priority(actions: Iterable[Mapping[str, Any]]) -> str:
        severities = {str(item.get("severity") or "low") for item in actions}
        if "critical" in severities:
            return "critical"
        if "high" in severities:
            return "high"
        if "medium" in severities:
            return "medium"
        if "low" in severities:
            return "low"
        return "none"
