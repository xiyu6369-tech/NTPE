from __future__ import annotations

from typing import Any, Dict, Mapping, Optional


class RuntimeSingleChunkShadowHook:
    """Single chunk shadow hook driven only by an injected metadata callback."""

    version = "TE-v4.3"
    stage = "4.3.3"
    name = "runtime_single_chunk_shadow_hook"

    forbidden_inputs = {
        "source_text",
        "translated_text",
        "text",
        "chunks",
        "api_key",
        "provider_client",
    }

    def invoke(
        self,
        request: Optional[Mapping[str, Any]] = None,
        admission_result: Optional[Mapping[str, Any]] = None,
        runtime_callback: Optional[Any] = None,
    ) -> Dict[str, Any]:
        request_data = dict(request or {}) if isinstance(request, Mapping) else {}
        admission = dict(admission_result or {}) if isinstance(admission_result, Mapping) else {}
        failed_checks = []
        callback_called = False
        shadow_result: Mapping[str, Any] = {}

        if not self._admitted(admission):
            failed_checks.append("admission_not_admitted")
        if not callable(runtime_callback):
            failed_checks.append("callback_missing")
        self._check_request(request_data, failed_checks)
        if self._has_forbidden_input(request_data):
            failed_checks.append("forbidden_input_present")

        if failed_checks:
            return self._result("shadow_hook_blocked", False, request_data, False, {}, failed_checks)

        try:
            raw = runtime_callback(self._callback_payload(request_data))
            callback_called = True
            if not isinstance(raw, Mapping):
                failed_checks.append("callback_result_invalid")
            else:
                shadow_result = raw
        except Exception as exc:  # noqa: BLE001 - hook failures are contained.
            callback_called = True
            failed_checks.append(f"callback_exception:{exc.__class__.__name__}")

        if failed_checks:
            return self._result("shadow_hook_failed", False, request_data, callback_called, {}, failed_checks)
        return self._result("shadow_hook_completed", True, request_data, callback_called, shadow_result, [])

    def is_completed(self, result: Optional[Mapping[str, Any]]) -> bool:
        return isinstance(result, Mapping) and result.get("status") == "shadow_hook_completed"

    def validate_result(self, result: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(result, Mapping):
            return False
        required = {
            "status",
            "completed",
            "stage",
            "runtime_id",
            "chunk_index",
            "callback_called",
            "shadow_result",
            "failed_checks",
            "result_replaced",
            "result_replacement_allowed",
            "provider_fallback_executed",
            "real_provider_request_executed",
            "rollback_available",
            "source_text_retained",
            "translated_text_retained",
            "metadata",
        }
        if not required.issubset(result):
            return False
        if result.get("stage") != self.stage:
            return False
        if result.get("status") not in {"shadow_hook_completed", "shadow_hook_blocked", "shadow_hook_failed"}:
            return False
        if not isinstance(result.get("failed_checks"), list):
            return False
        for key in (
            "result_replaced",
            "result_replacement_allowed",
            "provider_fallback_executed",
            "real_provider_request_executed",
            "source_text_retained",
            "translated_text_retained",
        ):
            if result.get(key) is not False:
                return False
        if result.get("rollback_available") is not True:
            return False
        if self._has_forbidden_input(result):
            return False
        if result.get("status") == "shadow_hook_completed":
            return result.get("completed") is True and result.get("callback_called") is True
        return result.get("completed") is False

    def _result(
        self,
        status: str,
        completed: bool,
        request: Mapping[str, Any],
        callback_called: bool,
        shadow_result: Mapping[str, Any],
        failed_checks: list[str],
    ) -> Dict[str, Any]:
        safe_shadow = self._sanitize(shadow_result)
        return {
            "status": status,
            "completed": completed,
            "stage": self.stage,
            "runtime_id": str(request.get("runtime_id") or ""),
            "chunk_index": self._safe_int(request.get("chunk_index")),
            "callback_called": callback_called,
            "shadow_result": {
                "runtime_status": str(safe_shadow.get("runtime_status") or ""),
                "recovery_recommended": safe_shadow.get("recovery_recommended") is True,
                "recommended_action": str(safe_shadow.get("recommended_action") or ""),
                "mock": bool(safe_shadow.get("mock", True)),
            },
            "failed_checks": list(failed_checks),
            "result_replaced": False,
            "result_replacement_allowed": False,
            "provider_fallback_executed": False,
            "real_provider_request_executed": False,
            "rollback_available": True,
            "source_text_retained": False,
            "translated_text_retained": False,
            "request_summary": self._request_summary(request),
            "metadata": {
                "hook": self.name,
                "version": self.version,
                "stage": self.stage,
                "callback_injected": True,
            },
        }

    def _check_request(self, request: Mapping[str, Any], failed_checks: list[str]) -> None:
        if not request:
            failed_checks.append("missing_request")
            return
        if request.get("caller") != "translation_runtime":
            failed_checks.append("invalid_caller")
        if request.get("hook_mode") != "shadow_only":
            failed_checks.append("invalid_hook_mode")
        if self._safe_int(request.get("chunk_count")) != 1:
            failed_checks.append("invalid_chunk_count")
        if self._safe_int(request.get("recovery_flow_count", 1)) > 1:
            failed_checks.append("recovery_flow_limit_exceeded")

    def _callback_payload(self, request: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "runtime_id": str(request.get("runtime_id") or ""),
            "session_id": str(request.get("session_id") or ""),
            "job_id": str(request.get("job_id") or ""),
            "chunk_index": self._safe_int(request.get("chunk_index")),
            "failure_outcome": str(request.get("failure_outcome") or ""),
            "retry_count": self._safe_int(request.get("retry_count")),
            "provider_attempts": self._safe_int(request.get("provider_attempts")),
            "latency_ms": self._safe_int(request.get("latency_ms")),
            "hook_mode": "shadow_only",
        }

    def _request_summary(self, request: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "runtime_id": str(request.get("runtime_id") or ""),
            "session_id": str(request.get("session_id") or ""),
            "job_id": str(request.get("job_id") or ""),
            "chunk_index": self._safe_int(request.get("chunk_index")),
            "failure_outcome": str(request.get("failure_outcome") or ""),
            "keys": sorted(str(key) for key in request if str(key) not in self.forbidden_inputs),
        }

    def _sanitize(self, value: Any) -> Any:
        if isinstance(value, Mapping):
            return {
                str(key): self._sanitize(nested)
                for key, nested in value.items()
                if str(key) not in self.forbidden_inputs
            }
        if isinstance(value, list):
            return [self._sanitize(item) for item in value]
        if isinstance(value, tuple):
            return tuple(self._sanitize(item) for item in value)
        return value

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
    def _admitted(admission: Mapping[str, Any]) -> bool:
        return (
            admission.get("admitted") is True
            and admission.get("status") == "admitted_for_runtime_shadow_hook"
        )

    @staticmethod
    def _safe_int(value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0


__all__ = ["RuntimeSingleChunkShadowHook"]
