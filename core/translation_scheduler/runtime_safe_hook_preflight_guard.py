from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .runtime_safe_hook_preflight_contract import RuntimeSafeHookPreflightContract


class RuntimeSafeHookPreflightGuard:
    """Validate safe hook preflight requests before any disabled trial path."""

    stage = "3.6.2"
    safety_boundaries = {
        "provider_runtime": "forbidden",
        "http_client": "forbidden",
        "api_key": "forbidden",
        "launcher_flow": "unchanged",
        "translation_runtime_flow": "unchanged",
        "real_translation": "forbidden",
    }

    def __init__(self, contract_builder: RuntimeSafeHookPreflightContract | None = None) -> None:
        self.contract_builder = contract_builder or RuntimeSafeHookPreflightContract()

    def guard(
        self,
        request: Mapping[str, Any] | None = None,
        contract: Mapping[str, Any] | None = None,
        flag_state: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        active_contract = dict(contract or self.contract_builder.build_contract())
        flag = dict(flag_state or {})
        request_data = dict(request or {})

        reason = self._block_reason(request_data, active_contract, flag)
        allowed = reason == "preflight_allowed"

        return {
            "allowed": allowed,
            "blocked": not allowed,
            "reason": reason,
            "stage": self.stage,
            "preflight_status": "allowed" if allowed else "blocked",
            "request_summary": self._request_summary(request_data),
            "safety_boundaries": dict(self.safety_boundaries),
            "metadata": {
                "guard": "runtime_safe_hook_preflight_guard",
                "contract_stage": active_contract.get("stage", "unknown"),
                "flag_source": flag.get("source", "missing"),
                "flag_reason": flag.get("reason", "missing_flag_state"),
                "runtime_touch_mode": active_contract.get("runtime_touch_mode", "unknown"),
                "launcher_touch_mode": active_contract.get("launcher_touch_mode", "unknown"),
                "provider_touch_mode": active_contract.get("provider_touch_mode", "unknown"),
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
            "unsafe_default_mode",
            "unsafe_enabled_mode",
            "unsafe_touch_mode",
            "real_translation_enabled",
            "runtime_integration_disabled",
            "preflight_allowed",
        }:
            errors.append("reason is invalid")
        if data.get("stage") != self.stage:
            errors.append("stage must be 3.6.2")
        if data.get("preflight_status") not in {"allowed", "blocked"}:
            errors.append("preflight_status must be allowed or blocked")
        if data.get("allowed") is True and data.get("preflight_status") != "allowed":
            errors.append("allowed result must have allowed preflight_status")
        if data.get("blocked") is True and data.get("preflight_status") != "blocked":
            errors.append("blocked result must have blocked preflight_status")
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
    ) -> str:
        if not request:
            return "missing_request"
        if contract.get("default_mode") != "disabled":
            return "unsafe_default_mode"
        if contract.get("enabled_mode") != "mock_only":
            return "unsafe_enabled_mode"
        if any(
            contract.get(key) != "none"
            for key in ("runtime_touch_mode", "launcher_touch_mode", "provider_touch_mode")
        ):
            return "unsafe_touch_mode"
        if contract.get("real_translation") is not False:
            return "real_translation_enabled"
        if flag_state.get("enabled") is not True:
            return "runtime_integration_disabled"
        return "preflight_allowed"

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


__all__ = ["RuntimeSafeHookPreflightGuard"]
