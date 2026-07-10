from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from .quality_runtime_gate_contract import QualityRuntimeGateContract


class QualityRuntimeGateAdmission:
    version = "TE-v5.2"
    stage = "5.2.2"

    _FORBIDDEN = {"api_key", "provider_client"}

    def __init__(self) -> None:
        self.contract = QualityRuntimeGateContract()

    def evaluate(
        self,
        request: Optional[Mapping[str, Any]] = None,
        contract: Optional[Mapping[str, Any]] = None,
        flag_state: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        req = dict(request or {})
        flag = dict(flag_state or {})
        failed = []

        if not request:
            failed.append("missing_request")
        if not contract:
            failed.append("missing_contract")
        elif not self.contract.validate_contract(contract):
            failed.append("invalid_contract")

        if flag.get("enabled") is not True:
            failed.append("feature_flag_disabled")
        if flag.get("mode") != "single_chunk_quality_gate":
            failed.append("invalid_flag_mode")

        if req.get("caller") != "translation_runtime":
            failed.append("invalid_caller")
        if req.get("gate_mode") != "single_chunk_quality_gate":
            failed.append("invalid_gate_mode")
        if not str(req.get("runtime_id") or "").strip():
            failed.append("missing_runtime_id")
        if int(req.get("chunk_index", 0) or 0) <= 0:
            failed.append("invalid_chunk_index")
        if int(req.get("chunk_count", 0) or 0) != 1:
            failed.append("invalid_chunk_count")
        if self._has_forbidden(req):
            failed.append("forbidden_input_present")

        admitted = not failed
        return {
            "admitted": admitted,
            "status": "admitted_for_quality_gate" if admitted else "rejected",
            "stage": self.stage,
            "reason": "all_admission_checks_passed" if admitted else failed[0],
            "failed_checks": failed,
            "request_summary": {
                "runtime_id": str(req.get("runtime_id") or ""),
                "chunk_index": int(req.get("chunk_index", 0) or 0),
                "chunk_count": int(req.get("chunk_count", 0) or 0),
                "caller": str(req.get("caller") or ""),
                "gate_mode": str(req.get("gate_mode") or ""),
                "keys": sorted(
                    str(key) for key in req.keys() if str(key) not in self._FORBIDDEN
                ),
                "has_forbidden_inputs": self._has_forbidden(req),
            },
            "execution_allowed": False,
            "provider_request_allowed": False,
            "real_translation_allowed": False,
            "result_replacement_allowed": False,
            "rollback_available": True,
        }

    def is_admitted(self, result: Optional[Mapping[str, Any]]) -> bool:
        return (
            isinstance(result, Mapping)
            and result.get("admitted") is True
            and result.get("status") == "admitted_for_quality_gate"
        )

    def validate_result(self, result: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(result, Mapping):
            return False
        required = {
            "admitted", "status", "stage", "reason", "failed_checks",
            "request_summary", "execution_allowed",
            "provider_request_allowed", "real_translation_allowed",
            "result_replacement_allowed", "rollback_available",
        }
        if not required.issubset(result):
            return False
        if result.get("stage") != self.stage:
            return False
        if result.get("execution_allowed") is not False:
            return False
        if result.get("provider_request_allowed") is not False:
            return False
        if result.get("real_translation_allowed") is not False:
            return False
        if result.get("result_replacement_allowed") is not False:
            return False
        if result.get("rollback_available") is not True:
            return False
        if result.get("admitted") is True:
            return result.get("status") == "admitted_for_quality_gate" and result.get("failed_checks") == []
        return result.get("status") == "rejected" and bool(result.get("failed_checks"))

    @classmethod
    def _has_forbidden(cls, value: Any) -> bool:
        if isinstance(value, Mapping):
            for key, item in value.items():
                if str(key) in cls._FORBIDDEN:
                    return True
                if cls._has_forbidden(item):
                    return True
        elif isinstance(value, (list, tuple)):
            return any(cls._has_forbidden(item) for item in value)
        return False
