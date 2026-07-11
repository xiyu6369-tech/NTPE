from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional

from .runtime_recovery_hook_contract import TranslationRuntimeRecoveryHookContract


class RuntimeHookAdmissionAdapter:
    """Admission adapter for translation-runtime shadow recovery hooks."""

    version = "TE-v4.3"
    stage = "4.3.2"
    name = "runtime_hook_admission_adapter"

    forbidden_inputs = {
        "source_text",
        "translated_text",
        "text",
        "chunks",
        "api_key",
        "provider_client",
    }

    def __init__(self) -> None:
        self.contract_builder = TranslationRuntimeRecoveryHookContract()

    def evaluate_hook_request(
        self,
        request: Optional[Mapping[str, Any]] = None,
        contract: Optional[Mapping[str, Any]] = None,
        readiness: Optional[Mapping[str, Any]] = None,
        flag_state: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        request_data = dict(request or {}) if isinstance(request, Mapping) else {}
        readiness_data = dict(readiness or {}) if isinstance(readiness, Mapping) else {}
        flag = dict(flag_state or {}) if isinstance(flag_state, Mapping) else {}
        failed_checks: List[str] = []

        if not isinstance(request, Mapping):
            failed_checks.append("missing_request")
        if not isinstance(contract, Mapping):
            failed_checks.append("missing_contract")
        elif not self.contract_builder.validate_contract(contract):
            failed_checks.append("invalid_contract")

        if readiness_data.get("approved") is not True or readiness_data.get("status") != "ready":
            failed_checks.append("readiness_not_approved")
        for freeze_key, check_name in (
            ("te_v40_freeze", "te_v40_freeze_missing"),
            ("te_v41_freeze", "te_v41_freeze_missing"),
            ("te_v42_freeze", "te_v42_freeze_missing"),
        ):
            if readiness_data.get(freeze_key) is not True:
                failed_checks.append(check_name)
        if flag.get("enabled") is not True:
            failed_checks.append("feature_flag_disabled")
        if flag.get("mode") not in {"runtime_shadow_hook", "shadow_only"}:
            failed_checks.append("invalid_flag_mode")

        self._check_request(request_data, failed_checks)
        has_forbidden = self._has_forbidden_input(request_data)
        if has_forbidden:
            failed_checks.append("forbidden_input_present")

        failed_checks = self._dedupe(failed_checks)
        admitted = not failed_checks
        return {
            "admitted": admitted,
            "status": "admitted_for_runtime_shadow_hook" if admitted else "rejected",
            "stage": self.stage,
            "reason": "all_hook_admission_checks_passed" if admitted else failed_checks[0],
            "failed_checks": failed_checks,
            "request_summary": self._request_summary(request_data, has_forbidden),
            "next_allowed_mode": "runtime_shadow_hook",
            "execution_allowed": False,
            "result_replacement_allowed": False,
            "provider_fallback_allowed": False,
            "real_provider_request_allowed": False,
            "real_translation_allowed": False,
            "rollback_available": True,
            "translation_runtime_touch_mode": "optional_hook_only",
            "provider_runtime_touch_mode": "none",
            "launcher_touch_mode": "none",
            "metadata": {
                "adapter": self.name,
                "version": self.version,
                "stage": self.stage,
                "external_reads": False,
            },
        }

    def is_admitted(self, result: Optional[Mapping[str, Any]]) -> bool:
        return (
            isinstance(result, Mapping)
            and result.get("admitted") is True
            and result.get("status") == "admitted_for_runtime_shadow_hook"
        )

    def validate_result(self, result: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(result, Mapping):
            return False
        required = {
            "admitted",
            "status",
            "stage",
            "reason",
            "failed_checks",
            "request_summary",
            "next_allowed_mode",
            "execution_allowed",
            "result_replacement_allowed",
            "provider_fallback_allowed",
            "real_provider_request_allowed",
            "real_translation_allowed",
            "rollback_available",
            "translation_runtime_touch_mode",
            "provider_runtime_touch_mode",
            "launcher_touch_mode",
            "metadata",
        }
        if not required.issubset(result):
            return False
        if result.get("stage") != self.stage:
            return False
        if result.get("next_allowed_mode") != "runtime_shadow_hook":
            return False
        for key in (
            "execution_allowed",
            "result_replacement_allowed",
            "provider_fallback_allowed",
            "real_provider_request_allowed",
            "real_translation_allowed",
        ):
            if result.get(key) is not False:
                return False
        if result.get("rollback_available") is not True:
            return False
        if result.get("translation_runtime_touch_mode") != "optional_hook_only":
            return False
        if result.get("provider_runtime_touch_mode") != "none":
            return False
        if result.get("launcher_touch_mode") != "none":
            return False
        failed = result.get("failed_checks")
        if not isinstance(failed, list):
            return False
        if result.get("admitted") is True:
            if result.get("status") != "admitted_for_runtime_shadow_hook" or failed:
                return False
        elif result.get("admitted") is False:
            if result.get("status") != "rejected" or not failed:
                return False
        else:
            return False
        summary = result.get("request_summary")
        if not isinstance(summary, Mapping):
            return False
        if self._has_forbidden_input(summary):
            return False
        return isinstance(result.get("metadata"), Mapping)

    def _check_request(self, request: Mapping[str, Any], failed_checks: List[str]) -> None:
        if not request:
            return
        if request.get("caller") != "translation_runtime":
            failed_checks.append("invalid_caller")
        if request.get("hook_mode") != "shadow_only":
            failed_checks.append("invalid_hook_mode")
        if not str(request.get("runtime_id") or "").strip():
            failed_checks.append("missing_runtime_id")
        if self._safe_int(request.get("chunk_index")) <= 0:
            failed_checks.append("invalid_chunk_index")
        if self._safe_int(request.get("chunk_count")) != 1:
            failed_checks.append("invalid_chunk_count")
        if self._safe_int(request.get("recovery_flow_count", 1)) > 1:
            failed_checks.append("recovery_flow_limit_exceeded")
        if not str(request.get("failure_outcome") or "").strip():
            failed_checks.append("missing_failure_outcome")

    def _request_summary(self, request: Mapping[str, Any], has_forbidden: bool) -> Dict[str, Any]:
        return {
            "runtime_id": str(request.get("runtime_id") or ""),
            "session_id": str(request.get("session_id") or ""),
            "job_id": str(request.get("job_id") or ""),
            "chunk_index": self._safe_int(request.get("chunk_index")),
            "chunk_count": self._safe_int(request.get("chunk_count")),
            "caller": str(request.get("caller") or ""),
            "hook_mode": str(request.get("hook_mode") or ""),
            "failure_outcome": str(request.get("failure_outcome") or ""),
            "provider_attempts": self._safe_int(request.get("provider_attempts")),
            "retry_count": self._safe_int(request.get("retry_count")),
            "latency_ms": self._safe_int(request.get("latency_ms")),
            "has_forbidden_inputs": has_forbidden,
            "keys": sorted(str(key) for key in request if str(key) not in self.forbidden_inputs),
        }

    def _has_forbidden_input(self, value: Any) -> bool:
        if isinstance(value, Mapping):
            for key, nested in value.items():
                if str(key) in self.forbidden_inputs:
                    return True
                if self._has_forbidden_input(nested):
                    return True
            return False
        if isinstance(value, (list, tuple)):
            return any(self._has_forbidden_input(item) for item in value)
        return False

    @staticmethod
    def _safe_int(value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _dedupe(values: Iterable[str]) -> List[str]:
        result = []
        for value in values:
            if value not in result:
                result.append(value)
        return result


__all__ = ["RuntimeHookAdmissionAdapter"]
