from __future__ import annotations

from typing import Any, Dict, Mapping, Optional


class SingleChunkControlledRecoveryExecutor:
    """Executes one injected metadata callback and creates a guarded candidate."""

    version = "TE-v4.4"
    stage = "4.4.3"
    name = "single_chunk_controlled_recovery_executor"
    forbidden_inputs = {"source_text", "translated_text", "text", "chunks", "api_key", "provider_client"}

    def execute(
        self,
        request: Optional[Mapping[str, Any]] = None,
        admission_result: Optional[Mapping[str, Any]] = None,
        recovery_callback: Optional[Any] = None,
    ) -> Dict[str, Any]:
        req = dict(request or {}) if isinstance(request, Mapping) else {}
        admission = dict(admission_result or {}) if isinstance(admission_result, Mapping) else {}
        failed = []
        called = False
        candidate: Mapping[str, Any] = {}
        if not self._admitted(admission):
            failed.append("admission_not_admitted")
        if not callable(recovery_callback):
            failed.append("callback_missing")
        if req.get("caller") != "translation_runtime":
            failed.append("invalid_caller")
        if req.get("execution_mode") != "single_chunk_controlled_recovery":
            failed.append("invalid_execution_mode")
        if self._int(req.get("chunk_count")) != 1:
            failed.append("invalid_chunk_count")
        if self._int(req.get("recovery_execution_count", 1)) > 1:
            failed.append("recovery_execution_limit_exceeded")
        if self._has_forbidden(req):
            failed.append("forbidden_input_present")
        if failed:
            return self._result("controlled_execution_blocked", False, req, False, {}, failed)
        try:
            raw = recovery_callback(self._payload(req))
            called = True
            if not isinstance(raw, Mapping):
                failed.append("callback_result_invalid")
            elif self._has_forbidden(raw):
                failed.append("callback_forbidden_input")
            else:
                candidate = raw
        except Exception as exc:  # noqa: BLE001 - isolated callbacks must be contained.
            called = True
            failed.append(f"callback_exception:{exc.__class__.__name__}")
        if failed:
            return self._result("controlled_execution_failed", False, req, called, {}, failed)
        success = candidate.get("outcome") == "success" and candidate.get("candidate_valid") is True
        status = "controlled_execution_completed" if success else "controlled_execution_failed"
        return self._result(status, success, req, called, candidate, [] if success else ["candidate_not_successful"])

    def is_completed(self, result: Optional[Mapping[str, Any]]) -> bool:
        return isinstance(result, Mapping) and result.get("status") == "controlled_execution_completed" and result.get("completed") is True

    def validate_result(self, result: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(result, Mapping):
            return False
        required = {
            "status", "completed", "success", "stage", "runtime_id", "chunk_index", "callback_called",
            "original_result_id", "recovery_candidate_id", "candidate_summary", "failed_checks",
            "original_result_preserved", "result_replaced", "replacement_pending_guard",
            "real_provider_request_executed", "provider_fallback_executed", "real_translation_executed",
            "rollback_available", "source_text_retained", "translated_text_retained", "metadata",
        }
        if not required.issubset(result) or result.get("stage") != self.stage:
            return False
        if result.get("status") not in {"controlled_execution_completed", "controlled_execution_failed", "controlled_execution_blocked"}:
            return False
        if result.get("original_result_preserved") is not True or result.get("rollback_available") is not True:
            return False
        if any(result.get(key) is not False for key in (
            "result_replaced", "real_provider_request_executed", "provider_fallback_executed",
            "real_translation_executed", "source_text_retained", "translated_text_retained",
        )):
            return False
        if self._has_forbidden(result):
            return False
        if result.get("status") == "controlled_execution_completed":
            return result.get("completed") is True and result.get("success") is True and result.get("replacement_pending_guard") is True
        return result.get("completed") is False and result.get("success") is False and result.get("replacement_pending_guard") is False

    def _result(self, status: str, success: bool, request: Mapping[str, Any], called: bool, candidate: Mapping[str, Any], failed: list[str]) -> Dict[str, Any]:
        return {
            "status": status,
            "completed": status == "controlled_execution_completed",
            "success": success,
            "stage": self.stage,
            "runtime_id": str(request.get("runtime_id") or ""),
            "chunk_index": self._int(request.get("chunk_index")),
            "callback_called": called,
            "original_result_id": str(request.get("original_result_id") or ""),
            "recovery_candidate_id": str(request.get("recovery_candidate_id") or ""),
            "candidate_summary": self._candidate_summary(candidate),
            "failed_checks": list(failed),
            "original_result_preserved": True,
            "result_replaced": False,
            "replacement_pending_guard": success,
            "real_provider_request_executed": False,
            "provider_fallback_executed": False,
            "real_translation_executed": False,
            "rollback_available": True,
            "source_text_retained": False,
            "translated_text_retained": False,
            "metadata": {"executor": self.name, "version": self.version, "stage": self.stage, "callback_injected": True},
        }

    def _payload(self, request: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "runtime_id": str(request.get("runtime_id") or ""),
            "chunk_index": self._int(request.get("chunk_index")),
            "original_result_id": str(request.get("original_result_id") or ""),
            "recovery_candidate_id": str(request.get("recovery_candidate_id") or ""),
            "failure_outcome": str(request.get("failure_outcome") or ""),
            "retry_count": self._int(request.get("retry_count")),
            "provider_attempts": self._int(request.get("provider_attempts")),
            "latency_ms": self._int(request.get("latency_ms")),
            "execution_mode": "single_chunk_controlled_recovery",
        }

    def _candidate_summary(self, candidate: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "outcome": str(candidate.get("outcome") or ""),
            "candidate_valid": candidate.get("candidate_valid") is True,
            "translated_chars": self._int(candidate.get("translated_chars")),
            "quality_pass": candidate.get("quality_pass") is True,
            "hangul_residue_count": self._int(candidate.get("hangul_residue_count")),
            "duplicate_count": self._int(candidate.get("duplicate_count")),
            "mock": candidate.get("mock") is True,
        }

    def _has_forbidden(self, value: Any) -> bool:
        if isinstance(value, Mapping):
            return any(str(key) in self.forbidden_inputs or self._has_forbidden(nested) for key, nested in value.items())
        if isinstance(value, (list, tuple)):
            return any(self._has_forbidden(item) for item in value)
        return False

    @staticmethod
    def _admitted(admission: Mapping[str, Any]) -> bool:
        return admission.get("admitted") is True and admission.get("status") == "admitted_for_controlled_execution" and admission.get("execution_allowed") is True

    @staticmethod
    def _int(value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0


__all__ = ["SingleChunkControlledRecoveryExecutor"]
