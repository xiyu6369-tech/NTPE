from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .controlled_runtime_trial_contract import ControlledRuntimeTrialContract


class ControlledRuntimeTrialAdmissionGate:
    """Fail-closed admission decision for a future isolated dry-run trial."""

    stage = "3.8.2"
    forbidden_inputs = frozenset({"source_text", "text", "chunks", "api_key", "provider_client"})
    required_result_fields = (
        "admitted",
        "status",
        "stage",
        "reason",
        "request_summary",
        "failed_checks",
        "next_allowed_mode",
        "execution_allowed",
        "real_runtime_allowed",
        "rollback_available",
        "provider_access",
        "http_access",
        "api_key_access",
        "launcher_touch_mode",
        "translation_runtime_touch_mode",
        "metadata",
    )

    def evaluate(
        self,
        request: Mapping[str, Any] | None = None,
        contract: Mapping[str, Any] | None = None,
        readiness_decision: Mapping[str, Any] | None = None,
        flag_state: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        request_data = dict(request) if isinstance(request, Mapping) else {}
        contract_data = dict(contract) if isinstance(contract, Mapping) else {}
        readiness = dict(readiness_decision) if isinstance(readiness_decision, Mapping) else {}
        flag = dict(flag_state) if isinstance(flag_state, Mapping) else {}
        forbidden_present = self._contains_forbidden_input(request_data)
        failed_checks: list[str] = []

        if not isinstance(request, Mapping) or not request_data:
            failed_checks.append("missing_request")

        if not isinstance(contract, Mapping):
            failed_checks.append("invalid_contract")
        else:
            validation = ControlledRuntimeTrialContract().validate_contract(contract_data)
            if validation.get("valid") is not True:
                failed_checks.append("invalid_contract")

        if contract_data.get("rollback_mode") != "immediate_disable":
            failed_checks.append("rollback_unavailable")

        safety_guarantees = contract_data.get("safety_guarantees")
        if (
            not isinstance(safety_guarantees, Mapping)
            or safety_guarantees.get("execution_allowed") is not False
            or safety_guarantees.get("real_runtime_allowed") is not False
        ):
            failed_checks.append("unsafe_execution_permission")

        readiness_safe = (
            readiness.get("approved") is True
            and readiness.get("decision") == "approved_for_mock_only"
            and readiness.get("next_allowed_mode") == "mock_only"
            and readiness.get("real_runtime_allowed") is False
            and readiness.get("execution_allowed") is False
        )
        if not readiness_safe:
            failed_checks.append("readiness_not_approved")
        if flag.get("enabled") is not True:
            failed_checks.append("feature_flag_disabled")
        if request_data.get("caller") != "translation_runtime":
            failed_checks.append("invalid_caller")
        if request_data.get("trial_mode") != "isolated_dry_run":
            failed_checks.append("invalid_trial_mode")
        if forbidden_present:
            failed_checks.append("forbidden_input_present")

        failed_checks = list(dict.fromkeys(failed_checks))
        admitted = not failed_checks
        status = "admitted_for_isolated_dry_run" if admitted else "rejected"
        reason = "all_admission_checks_passed" if admitted else failed_checks[0]
        return {
            "admitted": admitted,
            "status": status,
            "stage": self.stage,
            "reason": reason,
            "request_summary": self._summarize_request(request_data, forbidden_present),
            "failed_checks": failed_checks,
            "next_allowed_mode": "isolated_dry_run",
            "execution_allowed": False,
            "real_runtime_allowed": False,
            "rollback_available": True,
            "provider_access": "forbidden",
            "http_access": "forbidden",
            "api_key_access": "forbidden",
            "launcher_touch_mode": "none",
            "translation_runtime_touch_mode": "none",
            "metadata": {
                "gate": "controlled_runtime_trial_admission_gate",
                "stage": self.stage,
                "decision_only": True,
            },
        }

    def is_admitted(self, result: Mapping[str, Any] | None) -> bool:
        data = dict(result or {})
        return data.get("admitted") is True and data.get("status") == "admitted_for_isolated_dry_run"

    def validate_result(self, result: Mapping[str, Any] | None) -> dict[str, Any]:
        data = dict(result or {})
        errors: list[str] = []
        for field in self.required_result_fields:
            if field not in data:
                errors.append(f"missing {field}")

        if data.get("stage") != self.stage:
            errors.append("stage must be 3.8.2")
        if data.get("next_allowed_mode") != "isolated_dry_run":
            errors.append("next_allowed_mode must be isolated_dry_run")
        if data.get("execution_allowed") is not False:
            errors.append("execution_allowed must be false")
        if data.get("real_runtime_allowed") is not False:
            errors.append("real_runtime_allowed must be false")
        if data.get("rollback_available") is not True:
            errors.append("rollback_available must be true")
        for key in ("provider_access", "http_access", "api_key_access"):
            if data.get(key) != "forbidden":
                errors.append(f"{key} must be forbidden")
        for key in ("launcher_touch_mode", "translation_runtime_touch_mode"):
            if data.get(key) != "none":
                errors.append(f"{key} must be none")

        admitted = data.get("admitted") is True
        if admitted and data.get("status") != "admitted_for_isolated_dry_run":
            errors.append("admitted result requires admitted_for_isolated_dry_run status")
        if not admitted and data.get("status") != "rejected":
            errors.append("non-admitted result requires rejected status")
        failed_checks = data.get("failed_checks")
        if not isinstance(failed_checks, list):
            errors.append("failed_checks list is required")
        elif admitted and failed_checks:
            errors.append("admitted result cannot contain failed_checks")

        summary = data.get("request_summary")
        if not isinstance(summary, Mapping):
            errors.append("request_summary mapping is required")
        elif self._contains_forbidden_input(summary):
            errors.append("request_summary contains forbidden input")
        if not isinstance(data.get("metadata"), Mapping):
            errors.append("metadata mapping is required")
        return {"valid": not errors, "errors": errors}

    def _contains_forbidden_input(self, value: Any) -> bool:
        if isinstance(value, Mapping):
            for key, nested_value in value.items():
                if str(key).lower() in self.forbidden_inputs:
                    return True
                if self._contains_forbidden_input(nested_value):
                    return True
            return False
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return any(self._contains_forbidden_input(item) for item in value)
        return False

    def _summarize_request(self, request: Mapping[str, Any], forbidden_present: bool) -> dict[str, Any]:
        raw_count = request.get("chunk_count", 0)
        chunk_count = raw_count if isinstance(raw_count, int) and not isinstance(raw_count, bool) and raw_count >= 0 else 0
        safe_keys = sorted(str(key) for key in request if str(key).lower() not in self.forbidden_inputs)
        return {
            "request_type": str(request.get("request_type", "unknown")),
            "runtime_id": str(request.get("runtime_id", "runtime-state-unknown")),
            "caller": str(request.get("caller", "unknown")),
            "trial_mode": str(request.get("trial_mode", "disabled")),
            "chunk_count": chunk_count,
            "has_forbidden_inputs": forbidden_present,
            "keys": safe_keys,
        }


__all__ = ["ControlledRuntimeTrialAdmissionGate"]
