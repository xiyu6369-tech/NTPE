from __future__ import annotations

from typing import Any, Dict, Mapping, Optional


class QualityRuntimeGateDecision:
    version = "TE-v5.2"
    stage = "5.2.3"

    def decide(
        self,
        admission_result: Optional[Mapping[str, Any]],
        repair_result: Optional[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        admission = dict(admission_result or {})
        repair = dict(repair_result or {})

        if admission.get("admitted") is not True:
            return self._result(
                decision="blocked",
                reason="admission_rejected",
                accepted=False,
                retry_required=False,
                repair_required=False,
                quality_score=0,
            )

        status = str(repair.get("status") or "")
        accepted = repair.get("accepted") is True
        retry_required = bool(
            (repair.get("retry_result") or {}).get("retry") is True
            or repair.get("retry_required") is True
        )
        repair_required = bool(
            repair.get("repair_required") is True
            or status in {"repair_required", "retry_planned"}
        )
        quality_score = int(
            (repair.get("quality_result") or {}).get("quality_score", 0) or 0
        )

        if accepted:
            decision = "accept"
            reason = "quality_pass"
        elif retry_required:
            decision = "retry"
            reason = "quality_retry_required"
        else:
            decision = "reject"
            reason = "quality_rejected"

        return self._result(
            decision=decision,
            reason=reason,
            accepted=accepted,
            retry_required=retry_required,
            repair_required=repair_required,
            quality_score=quality_score,
        )

    def validate_result(self, result: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(result, Mapping):
            return False
        required = {
            "stage", "decision", "reason", "accepted",
            "retry_required", "repair_required", "quality_score",
            "runtime_result_unchanged", "provider_called",
            "http_called", "api_key_accessed",
            "real_translation_executed", "rollback_available",
        }
        if not required.issubset(result):
            return False
        if result.get("stage") != self.stage:
            return False
        if result.get("decision") not in {"blocked", "accept", "reject", "retry"}:
            return False
        for key in (
            "provider_called", "http_called",
            "api_key_accessed", "real_translation_executed",
        ):
            if result.get(key) is not False:
                return False
        return (
            result.get("runtime_result_unchanged") is True
            and result.get("rollback_available") is True
        )

    def should_accept(self, result: Optional[Mapping[str, Any]]) -> bool:
        return (
            isinstance(result, Mapping)
            and result.get("decision") == "accept"
            and result.get("accepted") is True
        )

    @staticmethod
    def _result(
        *,
        decision: str,
        reason: str,
        accepted: bool,
        retry_required: bool,
        repair_required: bool,
        quality_score: int,
    ) -> Dict[str, Any]:
        return {
            "stage": "5.2.3",
            "decision": decision,
            "reason": reason,
            "accepted": accepted,
            "retry_required": retry_required,
            "repair_required": repair_required,
            "quality_score": quality_score,
            "runtime_result_unchanged": True,
            "provider_called": False,
            "http_called": False,
            "api_key_accessed": False,
            "real_translation_executed": False,
            "rollback_available": True,
        }
