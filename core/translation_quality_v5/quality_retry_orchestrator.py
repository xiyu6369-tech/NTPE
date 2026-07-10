from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from core.translation_reliability import AdaptiveRetryPolicy


class QualityRetryOrchestrator:
    version = "TE-v5.1"
    stage = "5.1.2"

    def __init__(self) -> None:
        self.policy = AdaptiveRetryPolicy()

    def build_retry_decision(
        self,
        repair_plan: Optional[Mapping[str, Any]],
        runtime_state: Optional[Mapping[str, Any]] = None,
        config: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        plan = dict(repair_plan or {})
        state = dict(runtime_state or {})
        cfg = dict(config or {})

        if plan.get("retry_required") is not True:
            return {
                "stage": self.stage,
                "retry": False,
                "reason": "quality_retry_not_required",
                "outcome": "quality_pass",
                "decision": {},
                "source_text_retained": False,
                "translated_text_retained": False,
            }

        outcome = self._map_outcome(plan)
        decision = self.policy.decide(
            {
                "outcome": outcome,
                "attempt": int(state.get("attempt", 0) or 0),
                "max_attempts": int(state.get("max_attempts", cfg.get("max_attempts", 5)) or 5),
                "timeout_seconds": int(state.get("timeout_seconds", cfg.get("timeout_seconds", 180)) or 180),
                "chunk_size": int(state.get("chunk_size", cfg.get("chunk_size", 600)) or 600),
            },
            {
                "max_attempts": int(cfg.get("max_attempts", 5) or 5),
                "base_delay_seconds": int(cfg.get("base_delay_seconds", 5) or 5),
                "max_delay_seconds": int(cfg.get("max_delay_seconds", 60) or 60),
                "base_timeout_seconds": int(cfg.get("timeout_seconds", 180) or 180),
                "max_timeout_seconds": int(cfg.get("max_timeout_seconds", 300) or 300),
                "base_chunk_size": int(cfg.get("chunk_size", 600) or 600),
                "min_chunk_size": int(cfg.get("min_chunk_size", 200) or 200),
                "allow_provider_switch": False,
            },
        )

        return {
            "stage": self.stage,
            "retry": decision.get("retry") is True,
            "reason": str(decision.get("reason") or "quality_retry_decision"),
            "outcome": outcome,
            "decision": decision,
            "source_text_retained": False,
            "translated_text_retained": False,
        }

    def validate_result(self, result: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(result, Mapping):
            return False
        required = {
            "stage", "retry", "reason", "outcome", "decision",
            "source_text_retained", "translated_text_retained"
        }
        return (
            required.issubset(result)
            and result.get("stage") == self.stage
            and result.get("source_text_retained") is False
            and result.get("translated_text_retained") is False
        )

    @staticmethod
    def _map_outcome(plan: Mapping[str, Any]) -> str:
        codes = {
            str(item.get("issue_code") or "")
            for item in plan.get("actions", [])
            if isinstance(item, Mapping)
        }
        if "empty_output" in codes:
            return "empty_output"
        if "too_short" in codes or "paragraph_omission_suspected" in codes or "sentence_omission_suspected" in codes:
            return "too_short"
        if "hangul_residue" in codes:
            return "hangul_residue"
        if "duplicate_paragraph" in codes or "duplicate_line" in codes:
            return "duplicate_output"
        return "unknown_failure"
