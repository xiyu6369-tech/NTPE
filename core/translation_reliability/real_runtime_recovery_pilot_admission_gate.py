from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from .real_runtime_recovery_pilot_contract import RealRuntimeRecoveryPilotContract


class RealRuntimeRecoveryPilotAdmissionGate:
    """Admission gate for a future single-chunk recovery pilot.

    The gate only makes a decision from caller-supplied metadata. It does not
    execute recovery flows, create provider requests, read environment values,
    or touch Translation Runtime, Provider Runtime, HTTP clients, API keys, or
    launcher code.
    """

    version = "TE-v4.2"
    stage = "4.2.2"
    name = "real_runtime_recovery_pilot_admission_gate"

    forbidden_inputs = {
        "source_text",
        "translated_text",
        "text",
        "chunks",
        "api_key",
        "provider_client",
    }

    def __init__(self) -> None:
        self.contract_builder = RealRuntimeRecoveryPilotContract()

    def evaluate(
        self,
        request: Optional[Mapping[str, Any]] = None,
        contract: Optional[Mapping[str, Any]] = None,
        readiness_state: Optional[Mapping[str, Any]] = None,
        flag_state: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        failed_checks: List[str] = []

        request_data = dict(request or {}) if isinstance(request, Mapping) else {}
        readiness = dict(readiness_state or {}) if isinstance(readiness_state, Mapping) else {}
        flag = dict(flag_state or {}) if isinstance(flag_state, Mapping) else {}

        if not isinstance(request, Mapping):
            failed_checks.append("missing_request")

        if not isinstance(contract, Mapping):
            failed_checks.append("missing_contract")
        elif not self.contract_builder.validate_contract(contract):
            failed_checks.append("invalid_contract")
        else:
            self._check_contract_scalars(contract, failed_checks)

        self._check_readiness(readiness, failed_checks)
        self._check_flag(flag, failed_checks)
        self._check_request(request_data, failed_checks)

        has_forbidden = self._has_forbidden_input(request_data)
        if has_forbidden:
            failed_checks.append("forbidden_input_present")

        failed_checks = self._dedupe(failed_checks)
        admitted = not failed_checks

        result = {
            "admitted": admitted,
            "status": "admitted_for_single_chunk_dry_run" if admitted else "rejected",
            "stage": self.stage,
            "reason": "all_admission_checks_passed" if admitted else failed_checks[0],
            "failed_checks": failed_checks,
            "request_summary": self._request_summary(request_data, has_forbidden),
            "next_allowed_mode": "single_chunk_dry_run",
            "execution_allowed": False,
            "real_provider_request_allowed": False,
            "real_translation_allowed": False,
            "rollback_available": True,
            "provider_runtime_touch_mode": "none",
            "translation_runtime_touch_mode": "none",
            "launcher_touch_mode": "none",
            "metadata": {
                "gate": self.name,
                "version": self.version,
                "stage": self.stage,
                "decision_source": "supplied_mapping",
                "external_reads": False,
            },
        }
        return result

    def is_admitted(self, result: Optional[Mapping[str, Any]]) -> bool:
        return (
            isinstance(result, Mapping)
            and result.get("admitted") is True
            and result.get("status") == "admitted_for_single_chunk_dry_run"
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
            "real_provider_request_allowed",
            "real_translation_allowed",
            "rollback_available",
            "provider_runtime_touch_mode",
            "translation_runtime_touch_mode",
            "launcher_touch_mode",
            "metadata",
        }
        if not required.issubset(result):
            return False
        if result.get("stage") != self.stage:
            return False
        if result.get("next_allowed_mode") != "single_chunk_dry_run":
            return False
        if result.get("execution_allowed") is not False:
            return False
        if result.get("real_provider_request_allowed") is not False:
            return False
        if result.get("real_translation_allowed") is not False:
            return False
        if result.get("rollback_available") is not True:
            return False
        for key in (
            "provider_runtime_touch_mode",
            "translation_runtime_touch_mode",
            "launcher_touch_mode",
        ):
            if result.get(key) != "none":
                return False

        failed_checks = result.get("failed_checks")
        if not isinstance(failed_checks, list):
            return False
        if result.get("admitted") is True:
            if result.get("status") != "admitted_for_single_chunk_dry_run":
                return False
            if failed_checks:
                return False
        elif result.get("admitted") is False:
            if result.get("status") != "rejected":
                return False
            if not failed_checks:
                return False
        else:
            return False

        summary = result.get("request_summary")
        if not isinstance(summary, Mapping):
            return False
        if self.forbidden_inputs.intersection(summary):
            return False
        if self._has_forbidden_input(summary):
            return False

        return isinstance(result.get("metadata"), Mapping)

    def _check_contract_scalars(
        self, contract: Mapping[str, Any], failed_checks: List[str]
    ) -> None:
        if contract.get("default_mode") != "disabled":
            failed_checks.append("invalid_contract")
        if contract.get("activation_mode") != "explicit_opt_in_only":
            failed_checks.append("invalid_contract")
        if contract.get("execution_mode") != "contract_only":
            failed_checks.append("invalid_contract")
        if contract.get("allowed_scope") != "single_chunk":
            failed_checks.append("invalid_contract")
        if contract.get("max_chunks_per_request") != 1:
            failed_checks.append("invalid_contract")
        if contract.get("max_recovery_flows_per_chunk") != 1:
            failed_checks.append("invalid_contract")
        if contract.get("rollback_mode") != "immediate_disable":
            failed_checks.append("rollback_unavailable")

    def _check_readiness(
        self, readiness: Mapping[str, Any], failed_checks: List[str]
    ) -> None:
        if readiness.get("approved") is not True or readiness.get("status") != "ready":
            failed_checks.append("readiness_not_approved")
        if readiness.get("te_v40_freeze") is not True:
            failed_checks.append("te_v40_freeze_missing")
        if readiness.get("te_v41_freeze") is not True:
            failed_checks.append("te_v41_freeze_missing")
        if readiness.get("execution_allowed") is not False:
            failed_checks.append("unsafe_execution_permission")
        if readiness.get("real_provider_request_allowed") is not False:
            failed_checks.append("unsafe_provider_permission")
        if readiness.get("real_translation_allowed") is not False:
            failed_checks.append("unsafe_translation_permission")

    def _check_flag(self, flag: Mapping[str, Any], failed_checks: List[str]) -> None:
        if flag.get("enabled") is not True:
            failed_checks.append("feature_flag_disabled")
        if flag.get("mode") != "single_chunk_dry_run":
            failed_checks.append("invalid_flag_mode")

    def _check_request(
        self, request: Mapping[str, Any], failed_checks: List[str]
    ) -> None:
        if not request:
            return
        if request.get("caller") != "translation_runtime":
            failed_checks.append("invalid_caller")
        if request.get("pilot_mode") != "single_chunk_dry_run":
            failed_checks.append("invalid_pilot_mode")
        if not str(request.get("runtime_id") or "").strip():
            failed_checks.append("missing_runtime_id")
        if not self._positive_int(request.get("chunk_index")):
            failed_checks.append("invalid_chunk_index")
        if int(request.get("chunk_count") or 0) != 1:
            failed_checks.append("invalid_chunk_count")
        if int(request.get("recovery_flow_count") or 0) > 1:
            failed_checks.append("recovery_flow_limit_exceeded")
        if not str(request.get("failure_outcome") or "").strip():
            failed_checks.append("missing_failure_outcome")

    def _request_summary(
        self, request: Mapping[str, Any], has_forbidden: bool
    ) -> Dict[str, Any]:
        safe_keys = [
            str(key)
            for key in request.keys()
            if str(key) not in self.forbidden_inputs
        ]
        return {
            "runtime_id": str(request.get("runtime_id") or ""),
            "chunk_index": int(request.get("chunk_index") or 0),
            "chunk_count": int(request.get("chunk_count") or 0),
            "recovery_flow_count": int(request.get("recovery_flow_count") or 0),
            "caller": str(request.get("caller") or ""),
            "pilot_mode": str(request.get("pilot_mode") or ""),
            "failure_outcome": str(request.get("failure_outcome") or ""),
            "provider_attempts": int(request.get("provider_attempts") or 0),
            "retry_count": int(request.get("retry_count") or 0),
            "latency_ms": int(request.get("latency_ms") or 0),
            "has_forbidden_inputs": has_forbidden,
            "keys": sorted(safe_keys),
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
    def _positive_int(value: Any) -> bool:
        try:
            return int(value) > 0
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _dedupe(values: Iterable[str]) -> List[str]:
        seen = set()
        result = []
        for value in values:
            if value not in seen:
                seen.add(value)
                result.append(value)
        return result


__all__ = ["RealRuntimeRecoveryPilotAdmissionGate"]
