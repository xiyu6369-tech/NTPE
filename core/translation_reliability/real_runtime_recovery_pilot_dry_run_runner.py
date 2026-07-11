from __future__ import annotations

from typing import Any, Dict, Mapping, Optional


class RealRuntimeRecoveryPilotDryRunRunner:
    """Single-chunk dry-run runner for the real-runtime recovery pilot.

    The runner only calls an injected metadata handler. It never sends source
    text, never imports provider clients, and never touches runtime or launcher
    code.
    """

    version = "TE-v4.2"
    stage = "4.2.4"
    name = "real_runtime_recovery_pilot_dry_run_runner"

    forbidden_inputs = {
        "source_text",
        "translated_text",
        "text",
        "chunks",
        "api_key",
        "provider_client",
    }

    def run(
        self,
        request: Optional[Mapping[str, Any]] = None,
        admission_result: Optional[Mapping[str, Any]] = None,
        handler: Optional[Any] = None,
    ) -> Dict[str, Any]:
        request_data = dict(request or {}) if isinstance(request, Mapping) else {}
        admission = dict(admission_result or {}) if isinstance(admission_result, Mapping) else {}
        failed_checks = []
        handler_called = False
        handler_error = ""
        raw_result: Mapping[str, Any] = {}

        if not self._admitted(admission):
            failed_checks.append("admission_not_admitted")
        if not callable(handler):
            failed_checks.append("handler_missing")
        self._check_request(request_data, failed_checks)
        has_forbidden = self._has_forbidden_input(request_data)
        if has_forbidden:
            failed_checks.append("forbidden_input_present")

        if failed_checks:
            return self._result(
                status="dry_run_blocked",
                completed=False,
                success=False,
                request=request_data,
                handler_called=False,
                outcome="blocked",
                failed_checks=self._dedupe(failed_checks),
                has_forbidden=has_forbidden,
            )

        payload = self._handler_payload(request_data)
        try:
            raw = handler(payload)
            handler_called = True
            if not isinstance(raw, Mapping):
                failed_checks.append("handler_result_invalid")
            else:
                raw_result = raw
        except Exception as exc:  # noqa: BLE001 - deliberately contained.
            handler_called = True
            handler_error = exc.__class__.__name__
            failed_checks.append("handler_exception")

        if failed_checks:
            return self._result(
                status="dry_run_failed",
                completed=True,
                success=False,
                request=request_data,
                handler_called=handler_called,
                outcome=handler_error or "handler_failed",
                failed_checks=self._dedupe(failed_checks),
                has_forbidden=False,
            )

        outcome = str(raw_result.get("outcome") or "unknown")
        success = outcome == "success"
        return self._result(
            status="dry_run_completed" if success else "dry_run_failed",
            completed=True,
            success=success,
            request=request_data,
            handler_called=handler_called,
            outcome=outcome,
            failed_checks=[] if success else ["handler_outcome_not_success"],
            handler_result=raw_result,
            has_forbidden=False,
        )

    def is_completed(self, result: Optional[Mapping[str, Any]]) -> bool:
        return (
            isinstance(result, Mapping)
            and result.get("completed") is True
            and result.get("status") in {"dry_run_completed", "dry_run_failed"}
        )

    def validate_result(self, result: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(result, Mapping):
            return False
        required = {
            "status",
            "completed",
            "success",
            "stage",
            "runtime_id",
            "chunk_index",
            "dry_run_mode",
            "handler_called",
            "result_summary",
            "failed_checks",
            "execution_allowed",
            "real_provider_request_allowed",
            "real_translation_allowed",
            "rollback_available",
            "source_text_retained",
            "translated_text_retained",
            "integration_status",
            "metadata",
        }
        if not required.issubset(result):
            return False
        if result.get("stage") != self.stage:
            return False
        if result.get("status") not in {
            "dry_run_completed",
            "dry_run_failed",
            "dry_run_blocked",
        }:
            return False
        if result.get("execution_allowed") is not False:
            return False
        if result.get("real_provider_request_allowed") is not False:
            return False
        if result.get("real_translation_allowed") is not False:
            return False
        if result.get("rollback_available") is not True:
            return False
        if result.get("source_text_retained") is not False:
            return False
        if result.get("translated_text_retained") is not False:
            return False
        if not isinstance(result.get("failed_checks"), list):
            return False
        integration = result.get("integration_status")
        if not isinstance(integration, Mapping):
            return False
        for key in (
            "provider_called",
            "http_called",
            "api_key_accessed",
            "runtime_modified",
            "launcher_modified",
            "real_translation_executed",
        ):
            if integration.get(key) is not False:
                return False
        if self._has_forbidden_input(result):
            return False
        if result.get("status") == "dry_run_completed":
            return result.get("completed") is True and result.get("success") is True
        if result.get("status") == "dry_run_failed":
            return result.get("completed") is True and result.get("success") is False
        return result.get("completed") is False and result.get("success") is False

    def _result(
        self,
        *,
        status: str,
        completed: bool,
        success: bool,
        request: Mapping[str, Any],
        handler_called: bool,
        outcome: str,
        failed_checks: list[str],
        has_forbidden: bool,
        handler_result: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        safe_result = dict(handler_result or {})
        source_chars = self._safe_int(request.get("source_chars"))
        return {
            "status": status,
            "completed": completed,
            "success": success,
            "stage": self.stage,
            "runtime_id": str(request.get("runtime_id") or ""),
            "chunk_index": self._safe_int(request.get("chunk_index")),
            "dry_run_mode": "injected_metadata_handler",
            "handler_called": handler_called,
            "result_summary": {
                "outcome": outcome,
                "source_chars": source_chars,
                "translated_chars": self._safe_int(safe_result.get("translated_chars")),
                "provider_attempts": self._safe_int(
                    safe_result.get("provider_attempts", request.get("provider_attempts"))
                ),
                "latency_ms": self._safe_int(safe_result.get("latency_ms")),
                "mock": bool(safe_result.get("mock", True)),
                "has_forbidden_inputs": has_forbidden,
            },
            "failed_checks": failed_checks,
            "execution_allowed": False,
            "real_provider_request_allowed": False,
            "real_translation_allowed": False,
            "rollback_available": True,
            "source_text_retained": False,
            "translated_text_retained": False,
            "integration_status": {
                "provider_called": False,
                "http_called": False,
                "api_key_accessed": False,
                "runtime_modified": False,
                "launcher_modified": False,
                "real_translation_executed": False,
            },
            "request_summary": self._request_summary(request, has_forbidden),
            "metadata": {
                "runner": self.name,
                "version": self.version,
                "stage": self.stage,
                "external_handler_required": True,
            },
        }

    def _check_request(self, request: Mapping[str, Any], failed_checks: list[str]) -> None:
        if not request:
            failed_checks.append("missing_request")
            return
        if request.get("caller") != "translation_runtime":
            failed_checks.append("invalid_caller")
        if request.get("pilot_mode") != "single_chunk_dry_run":
            failed_checks.append("invalid_pilot_mode")
        if self._safe_int(request.get("chunk_count")) != 1:
            failed_checks.append("invalid_chunk_count")
        if self._safe_int(request.get("recovery_flow_count")) > 1:
            failed_checks.append("recovery_flow_limit_exceeded")

    def _handler_payload(self, request: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "runtime_id": str(request.get("runtime_id") or ""),
            "chunk_index": self._safe_int(request.get("chunk_index")),
            "source_chars": self._safe_int(request.get("source_chars")),
            "failure_outcome": str(request.get("failure_outcome") or ""),
            "dry_run_payload_id": str(request.get("dry_run_payload_id") or ""),
        }

    def _request_summary(self, request: Mapping[str, Any], has_forbidden: bool) -> Dict[str, Any]:
        return {
            "runtime_id": str(request.get("runtime_id") or ""),
            "chunk_index": self._safe_int(request.get("chunk_index")),
            "chunk_count": self._safe_int(request.get("chunk_count")),
            "recovery_flow_count": self._safe_int(request.get("recovery_flow_count")),
            "caller": str(request.get("caller") or ""),
            "pilot_mode": str(request.get("pilot_mode") or ""),
            "failure_outcome": str(request.get("failure_outcome") or ""),
            "dry_run_payload_id": str(request.get("dry_run_payload_id") or ""),
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
    def _admitted(admission: Mapping[str, Any]) -> bool:
        return (
            admission.get("admitted") is True
            and admission.get("status") == "admitted_for_single_chunk_dry_run"
        )

    @staticmethod
    def _safe_int(value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _dedupe(values: list[str]) -> list[str]:
        result = []
        for value in values:
            if value not in result:
                result.append(value)
        return result


__all__ = ["RealRuntimeRecoveryPilotDryRunRunner"]
