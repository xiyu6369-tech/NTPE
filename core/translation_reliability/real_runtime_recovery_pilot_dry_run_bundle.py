from __future__ import annotations

from typing import Any, Dict, Mapping, Optional


class RealRuntimeRecoveryPilotDryRunBundle:
    """Safe summary bundle for pilot admission, dry-run, and rollback results."""

    version = "TE-v4.2"
    stage = "4.2.5"
    name = "real_runtime_recovery_pilot_dry_run_bundle"

    forbidden_inputs = {
        "source_text",
        "translated_text",
        "text",
        "chunks",
        "api_key",
        "provider_client",
    }

    def build(
        self,
        runtime_id: str,
        admission_result: Optional[Mapping[str, Any]],
        dry_run_result: Optional[Mapping[str, Any]],
        rollback_result: Optional[Mapping[str, Any]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        admission = dict(admission_result or {}) if isinstance(admission_result, Mapping) else {}
        dry_run = dict(dry_run_result or {}) if isinstance(dry_run_result, Mapping) else {}
        rollback = dict(rollback_result or {}) if isinstance(rollback_result, Mapping) else {}

        status = self._status(admission, dry_run, rollback)
        successful = status == "pilot_dry_run_succeeded"

        return {
            "status": status,
            "successful": successful,
            "stage": self.stage,
            "runtime_id": str(runtime_id or ""),
            "admission_summary": self._admission_summary(admission),
            "dry_run_summary": self._dry_run_summary(dry_run),
            "rollback_summary": self._rollback_summary(rollback),
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
            "metadata": self._sanitize_metadata(metadata or {}),
        }

    def is_successful(self, bundle: Optional[Mapping[str, Any]]) -> bool:
        return (
            isinstance(bundle, Mapping)
            and bundle.get("successful") is True
            and bundle.get("status") == "pilot_dry_run_succeeded"
        )

    def validate_bundle(self, bundle: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(bundle, Mapping):
            return False
        required = {
            "status",
            "successful",
            "stage",
            "runtime_id",
            "admission_summary",
            "dry_run_summary",
            "rollback_summary",
            "execution_allowed",
            "real_provider_request_allowed",
            "real_translation_allowed",
            "rollback_available",
            "source_text_retained",
            "translated_text_retained",
            "integration_status",
            "metadata",
        }
        if not required.issubset(bundle):
            return False
        if bundle.get("stage") != self.stage:
            return False
        if bundle.get("status") not in {
            "pilot_dry_run_succeeded",
            "pilot_admission_rejected",
            "pilot_dry_run_blocked",
            "pilot_dry_run_failed",
            "pilot_rolled_back",
            "pilot_bundle_invalid",
        }:
            return False
        if bundle.get("execution_allowed") is not False:
            return False
        if bundle.get("real_provider_request_allowed") is not False:
            return False
        if bundle.get("real_translation_allowed") is not False:
            return False
        if bundle.get("rollback_available") is not True:
            return False
        if bundle.get("source_text_retained") is not False:
            return False
        if bundle.get("translated_text_retained") is not False:
            return False
        integration = bundle.get("integration_status")
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
        if self._has_forbidden_input(bundle):
            return False
        if bundle.get("status") == "pilot_dry_run_succeeded":
            return bundle.get("successful") is True
        return bundle.get("successful") is False

    def _status(
        self,
        admission: Mapping[str, Any],
        dry_run: Mapping[str, Any],
        rollback: Mapping[str, Any],
    ) -> str:
        if rollback and rollback.get("rolled_back") is True:
            return "pilot_rolled_back"
        if not admission or not dry_run:
            return "pilot_bundle_invalid"
        if admission.get("admitted") is not True:
            return "pilot_admission_rejected"
        if dry_run.get("status") == "dry_run_blocked":
            return "pilot_dry_run_blocked"
        if dry_run.get("status") == "dry_run_completed" and dry_run.get("success") is True:
            return "pilot_dry_run_succeeded"
        return "pilot_dry_run_failed"

    def _admission_summary(self, value: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "admitted": value.get("admitted") is True,
            "status": str(value.get("status") or ""),
            "reason": str(value.get("reason") or ""),
            "failed_checks": list(value.get("failed_checks") or []),
        }

    def _dry_run_summary(self, value: Mapping[str, Any]) -> Dict[str, Any]:
        summary = value.get("result_summary")
        if not isinstance(summary, Mapping):
            summary = {}
        return {
            "status": str(value.get("status") or ""),
            "completed": value.get("completed") is True,
            "success": value.get("success") is True,
            "handler_called": value.get("handler_called") is True,
            "outcome": str(summary.get("outcome") or ""),
            "source_chars": self._safe_int(summary.get("source_chars")),
            "translated_chars": self._safe_int(summary.get("translated_chars")),
            "provider_attempts": self._safe_int(summary.get("provider_attempts")),
            "latency_ms": self._safe_int(summary.get("latency_ms")),
        }

    def _rollback_summary(self, value: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "rolled_back": value.get("rolled_back") is True,
            "status": str(value.get("status") or ""),
            "current_mode": str(value.get("current_mode") or ""),
            "rollback_complete": value.get("rollback_complete") is True,
        }

    def _sanitize_metadata(self, value: Any) -> Any:
        if isinstance(value, Mapping):
            return {
                str(key): self._sanitize_metadata(nested)
                for key, nested in value.items()
                if str(key) not in self.forbidden_inputs
            }
        if isinstance(value, list):
            return [self._sanitize_metadata(item) for item in value]
        if isinstance(value, tuple):
            return tuple(self._sanitize_metadata(item) for item in value)
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
    def _safe_int(value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0


__all__ = ["RealRuntimeRecoveryPilotDryRunBundle"]
