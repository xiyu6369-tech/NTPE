from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional

from .controlled_execution_contract import ControlledExecutionContract


class ControlledExecutionAdmissionGate:
    """Fail-closed admission gate for isolated single-chunk recovery."""

    version = "TE-v4.4"
    stage = "4.4.2"
    name = "controlled_execution_admission_gate"
    forbidden_inputs = set(ControlledExecutionContract.forbidden_inputs)

    def __init__(self) -> None:
        self.contract_builder = ControlledExecutionContract()

    def evaluate(
        self,
        request: Optional[Mapping[str, Any]] = None,
        contract: Optional[Mapping[str, Any]] = None,
        readiness: Optional[Mapping[str, Any]] = None,
        flag_state: Optional[Mapping[str, Any]] = None,
        shadow_mapping: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        req = dict(request or {}) if isinstance(request, Mapping) else {}
        ready = dict(readiness or {}) if isinstance(readiness, Mapping) else {}
        flag = dict(flag_state or {}) if isinstance(flag_state, Mapping) else {}
        shadow = dict(shadow_mapping or {}) if isinstance(shadow_mapping, Mapping) else {}
        failed: List[str] = []

        if not isinstance(request, Mapping):
            failed.append("missing_request")
        if not isinstance(contract, Mapping):
            failed.append("missing_contract")
        elif not self.contract_builder.validate_contract(contract):
            failed.append("invalid_contract")
        if ready.get("approved") is not True or ready.get("status") != "ready_for_controlled_execution":
            failed.append("readiness_not_approved")
        for key, code in (
            ("te_v40_freeze", "te_v40_freeze_missing"),
            ("te_v41_freeze", "te_v41_freeze_missing"),
            ("te_v42_freeze", "te_v42_freeze_missing"),
            ("te_v43_freeze", "te_v43_freeze_missing"),
        ):
            if ready.get(key) is not True:
                failed.append(code)
        if ready.get("real_provider_request_allowed") is not False:
            failed.append("unsafe_provider_permission")
        if ready.get("provider_fallback_allowed") is not False:
            failed.append("unsafe_fallback_permission")
        if ready.get("real_translation_allowed") is not False:
            failed.append("unsafe_translation_permission")
        if flag.get("enabled") is not True:
            failed.append("feature_flag_disabled")
        if flag.get("mode") != "single_chunk_controlled_recovery":
            failed.append("invalid_flag_mode")
        if shadow.get("status") != "shadow_recommendation_available" or shadow.get("recovery_recommended") is not True:
            failed.append("shadow_recommendation_missing")
        if shadow.get("result_replacement_allowed") is not False or shadow.get("original_runtime_result_unchanged") is not True:
            failed.append("unsafe_shadow_mapping")
        if shadow.get("provider_fallback_executed") is not False or shadow.get("real_provider_request_executed") is not False:
            failed.append("unsafe_shadow_execution")

        self._check_request(req, failed)
        forbidden = self._has_forbidden(req)
        if forbidden:
            failed.append("forbidden_input_present")
        failed = self._dedupe(failed)
        admitted = not failed
        return {
            "admitted": admitted,
            "status": "admitted_for_controlled_execution" if admitted else "rejected",
            "stage": self.stage,
            "reason": "all_controlled_admission_checks_passed" if admitted else failed[0],
            "failed_checks": failed,
            "request_summary": self._summary(req, forbidden),
            "next_allowed_mode": "single_chunk_controlled_recovery",
            "execution_allowed": admitted,
            "real_provider_request_allowed": False,
            "provider_fallback_allowed": False,
            "real_translation_allowed": False,
            "result_replacement_allowed": False,
            "replacement_requires_guard": True,
            "rollback_available": True,
            "metadata": {"gate": self.name, "version": self.version, "stage": self.stage},
        }

    def is_admitted(self, result: Optional[Mapping[str, Any]]) -> bool:
        return isinstance(result, Mapping) and result.get("admitted") is True and result.get("status") == "admitted_for_controlled_execution"

    def validate_result(self, result: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(result, Mapping):
            return False
        required = {
            "admitted", "status", "stage", "reason", "failed_checks", "request_summary",
            "next_allowed_mode", "execution_allowed", "real_provider_request_allowed",
            "provider_fallback_allowed", "real_translation_allowed", "result_replacement_allowed",
            "replacement_requires_guard", "rollback_available", "metadata",
        }
        if not required.issubset(result) or result.get("stage") != self.stage:
            return False
        if result.get("next_allowed_mode") != "single_chunk_controlled_recovery":
            return False
        if any(result.get(key) is not False for key in (
            "real_provider_request_allowed", "provider_fallback_allowed", "real_translation_allowed", "result_replacement_allowed"
        )):
            return False
        if result.get("replacement_requires_guard") is not True or result.get("rollback_available") is not True:
            return False
        failed = result.get("failed_checks")
        if not isinstance(failed, list):
            return False
        if result.get("admitted") is True:
            if result.get("status") != "admitted_for_controlled_execution" or result.get("execution_allowed") is not True or failed:
                return False
        elif result.get("admitted") is False:
            if result.get("status") != "rejected" or result.get("execution_allowed") is not False or not failed:
                return False
        else:
            return False
        return not self._has_forbidden(result) and isinstance(result.get("metadata"), Mapping)

    def _check_request(self, request: Mapping[str, Any], failed: List[str]) -> None:
        if not request:
            return
        checks = (
            (request.get("caller") == "translation_runtime", "invalid_caller"),
            (request.get("execution_mode") == "single_chunk_controlled_recovery", "invalid_execution_mode"),
            (bool(str(request.get("runtime_id") or "").strip()), "missing_runtime_id"),
            (self._int(request.get("chunk_index")) > 0, "invalid_chunk_index"),
            (self._int(request.get("chunk_count")) == 1, "invalid_chunk_count"),
            (self._int(request.get("recovery_execution_count", 1)) <= 1, "recovery_execution_limit_exceeded"),
            (bool(str(request.get("original_result_id") or "").strip()), "missing_original_result_id"),
            (bool(str(request.get("recovery_candidate_id") or "").strip()), "missing_recovery_candidate_id"),
            (bool(str(request.get("failure_outcome") or "").strip()), "missing_failure_outcome"),
        )
        for condition, code in checks:
            if not condition:
                failed.append(code)

    def _summary(self, request: Mapping[str, Any], forbidden: bool) -> Dict[str, Any]:
        return {
            "runtime_id": str(request.get("runtime_id") or ""),
            "chunk_index": self._int(request.get("chunk_index")),
            "chunk_count": self._int(request.get("chunk_count")),
            "recovery_execution_count": self._int(request.get("recovery_execution_count")),
            "caller": str(request.get("caller") or ""),
            "execution_mode": str(request.get("execution_mode") or ""),
            "original_result_id": str(request.get("original_result_id") or ""),
            "recovery_candidate_id": str(request.get("recovery_candidate_id") or ""),
            "failure_outcome": str(request.get("failure_outcome") or ""),
            "has_forbidden_inputs": forbidden,
            "keys": sorted(str(key) for key in request if str(key) not in self.forbidden_inputs),
        }

    def _has_forbidden(self, value: Any) -> bool:
        if isinstance(value, Mapping):
            return any(str(key) in self.forbidden_inputs or self._has_forbidden(nested) for key, nested in value.items())
        if isinstance(value, (list, tuple)):
            return any(self._has_forbidden(item) for item in value)
        return False

    @staticmethod
    def _int(value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _dedupe(values: Iterable[str]) -> List[str]:
        return list(dict.fromkeys(values))


__all__ = ["ControlledExecutionAdmissionGate"]
