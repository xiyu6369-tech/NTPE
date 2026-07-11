from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .runtime_optin_hook_contract import RuntimeOptInHookContract


class RuntimeOptInHookGuard:
    """Validate optional runtime hook requests before any integration path."""

    stage = "3.4.2"
    safety_boundaries = {
        "provider_runtime": "external",
        "http_client": "forbidden",
        "api_key": "forbidden",
        "launcher_flow": "unchanged",
        "translation_runtime_flow": "unchanged",
        "real_translation": "forbidden",
    }

    def __init__(self, contract_builder: RuntimeOptInHookContract | None = None) -> None:
        self.contract_builder = contract_builder or RuntimeOptInHookContract()

    def guard(
        self,
        request: Mapping[str, Any] | None = None,
        contract: Mapping[str, Any] | None = None,
        flag_state: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        active_contract = dict(contract or self.contract_builder.build_contract())
        flag = dict(flag_state or {})
        request_data = dict(request or {})
        caller = str(request_data.get("caller", "unknown"))

        reason = self._block_reason(request_data, active_contract, flag, caller)
        allowed = reason == "hook_allowed"

        return {
            "allowed": allowed,
            "blocked": not allowed,
            "reason": reason,
            "stage": self.stage,
            "caller": caller,
            "request_summary": self._request_summary(request_data),
            "safety_boundaries": dict(self.safety_boundaries),
            "metadata": {
                "guard": "runtime_optin_hook_guard",
                "contract_stage": active_contract.get("stage", "unknown"),
                "flag_source": flag.get("source", "missing"),
                "flag_reason": flag.get("reason", "missing_flag_state"),
            },
        }

    def is_allowed(self, result: Mapping[str, Any] | None) -> bool:
        data = dict(result or {})
        return data.get("allowed") is True and data.get("blocked") is False

    def validate_guard_result(self, result: Mapping[str, Any] | None) -> dict[str, Any]:
        data = dict(result or {})
        errors: list[str] = []

        if not isinstance(data.get("allowed"), bool):
            errors.append("allowed boolean is required")
        if not isinstance(data.get("blocked"), bool):
            errors.append("blocked boolean is required")
        if data.get("allowed") == data.get("blocked"):
            errors.append("allowed and blocked must be opposites")
        if data.get("reason") not in {
            "missing_request",
            "invalid_caller",
            "runtime_integration_disabled",
            "non_mock_execution_mode",
            "hook_allowed",
        }:
            errors.append("reason is invalid")
        if data.get("stage") != self.stage:
            errors.append("stage must be 3.4.2")
        if not isinstance(data.get("caller"), str):
            errors.append("caller string is required")
        if not isinstance(data.get("request_summary"), Mapping):
            errors.append("request_summary mapping is required")

        boundaries = data.get("safety_boundaries")
        if not isinstance(boundaries, Mapping):
            errors.append("safety_boundaries mapping is required")
            boundaries = {}
        for key, expected in self.safety_boundaries.items():
            if boundaries.get(key) != expected:
                errors.append(f"{key} boundary must be {expected}")

        if not isinstance(data.get("metadata"), Mapping):
            errors.append("metadata mapping is required")

        return {"valid": not errors, "errors": errors}

    def _block_reason(
        self,
        request: Mapping[str, Any],
        contract: Mapping[str, Any],
        flag_state: Mapping[str, Any],
        caller: str,
    ) -> str:
        if not request:
            return "missing_request"
        allowed_callers = contract.get("allowed_callers", [])
        if caller not in allowed_callers:
            return "invalid_caller"
        if flag_state.get("enabled") is not True:
            return "runtime_integration_disabled"
        if contract.get("execution_mode") != "mock_only":
            return "non_mock_execution_mode"
        return "hook_allowed"

    def _request_summary(self, request: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "request_type": str(request.get("type", request.get("request_type", "unknown"))),
            "runtime_id": str(request.get("runtime_id", "runtime-state-unknown")),
            "chunk_count": self._chunk_count(request),
            "has_source_text": any(key in request for key in ("source_text", "text", "chunks")),
            "keys": sorted(str(key) for key in request if key not in {"source_text", "text", "chunks"}),
        }

    def _chunk_count(self, request: Mapping[str, Any]) -> int:
        chunks = request.get("chunks")
        if isinstance(chunks, Sequence) and not isinstance(chunks, (str, bytes, bytearray)):
            return len(chunks)
        if "source_text" in request or "text" in request:
            return 1
        return 0


__all__ = ["RuntimeOptInHookGuard"]
