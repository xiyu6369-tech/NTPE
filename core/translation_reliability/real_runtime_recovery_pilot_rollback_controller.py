from __future__ import annotations

from typing import Any, Dict, Mapping, Optional


class RealRuntimeRecoveryPilotRollbackController:
    """Idempotent rollback controller for the real-runtime recovery pilot.

    Stage 4.2.3 only derives a safe rollback result from caller-supplied
    metadata. It does not call admission gates, recovery flows, retry harnesses,
    providers, HTTP clients, API keys, Translation Runtime, or launcher code.
    """

    version = "TE-v4.2"
    stage = "4.2.3"
    name = "real_runtime_recovery_pilot_rollback_controller"

    forbidden_inputs = {
        "source_text",
        "translated_text",
        "text",
        "chunks",
        "api_key",
        "provider_client",
    }

    def request_rollback(
        self,
        state: Optional[Mapping[str, Any]] = None,
        reason: Optional[Any] = None,
    ) -> Dict[str, Any]:
        state_data = dict(state or {}) if isinstance(state, Mapping) else {}
        previous_mode = self._previous_mode(state_data)
        had_forbidden = self._has_forbidden_input(state_data)

        already_disabled = previous_mode == "disabled"
        rollback_reason = self._safe_reason(
            reason,
            "already_disabled" if already_disabled else "rollback_requested",
        )

        result = {
            "rolled_back": True,
            "status": "already_disabled" if already_disabled else "rolled_back",
            "stage": self.stage,
            "reason": rollback_reason,
            "previous_mode": previous_mode,
            "current_mode": "disabled",
            "pilot_status": "disabled",
            "admission_status": "revoked",
            "execution_allowed": False,
            "real_provider_request_allowed": False,
            "real_translation_allowed": False,
            "rollback_available": True,
            "rollback_complete": True,
            "provider_runtime_touch_mode": "none",
            "translation_runtime_touch_mode": "none",
            "launcher_touch_mode": "none",
            "source_text_retained": False,
            "translated_text_retained": False,
            "state_summary": self._state_summary(state_data, previous_mode, had_forbidden),
            "metadata": {
                "controller": self.name,
                "version": self.version,
                "stage": self.stage,
                "idempotent": True,
                "external_actions_executed": False,
                "provider_called": False,
                "http_called": False,
                "api_key_accessed": False,
                "runtime_modified": False,
                "launcher_modified": False,
                "admission_gate_called": False,
                "recovery_flow_called": False,
                "retry_harness_executed": False,
            },
        }
        return result

    def is_rolled_back(self, result: Optional[Mapping[str, Any]]) -> bool:
        return (
            isinstance(result, Mapping)
            and result.get("rolled_back") is True
            and result.get("current_mode") == "disabled"
            and result.get("pilot_status") == "disabled"
            and result.get("execution_allowed") is False
            and result.get("real_provider_request_allowed") is False
            and result.get("real_translation_allowed") is False
            and result.get("rollback_complete") is True
        )

    def validate_result(self, result: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(result, Mapping):
            return False

        required = {
            "rolled_back",
            "status",
            "stage",
            "reason",
            "previous_mode",
            "current_mode",
            "pilot_status",
            "admission_status",
            "execution_allowed",
            "real_provider_request_allowed",
            "real_translation_allowed",
            "rollback_available",
            "rollback_complete",
            "provider_runtime_touch_mode",
            "translation_runtime_touch_mode",
            "launcher_touch_mode",
            "source_text_retained",
            "translated_text_retained",
            "state_summary",
            "metadata",
        }
        if not required.issubset(result):
            return False
        if result.get("stage") != self.stage:
            return False
        if result.get("rolled_back") is not True:
            return False
        if result.get("status") not in {"rolled_back", "already_disabled"}:
            return False
        if result.get("current_mode") != "disabled":
            return False
        if result.get("pilot_status") != "disabled":
            return False
        if result.get("admission_status") != "revoked":
            return False
        if result.get("execution_allowed") is not False:
            return False
        if result.get("real_provider_request_allowed") is not False:
            return False
        if result.get("real_translation_allowed") is not False:
            return False
        if result.get("rollback_available") is not True:
            return False
        if result.get("rollback_complete") is not True:
            return False
        for key in (
            "provider_runtime_touch_mode",
            "translation_runtime_touch_mode",
            "launcher_touch_mode",
        ):
            if result.get(key) != "none":
                return False
        if result.get("source_text_retained") is not False:
            return False
        if result.get("translated_text_retained") is not False:
            return False

        metadata = result.get("metadata")
        if not isinstance(metadata, Mapping):
            return False
        expected_false = {
            "external_actions_executed",
            "provider_called",
            "http_called",
            "api_key_accessed",
            "runtime_modified",
            "launcher_modified",
            "admission_gate_called",
            "recovery_flow_called",
            "retry_harness_executed",
        }
        for key in expected_false:
            if metadata.get(key) is not False:
                return False
        if metadata.get("idempotent") is not True:
            return False

        summary = result.get("state_summary")
        if not isinstance(summary, Mapping):
            return False
        if self.forbidden_inputs.intersection(summary):
            return False
        if self._has_forbidden_input(summary):
            return False
        if self._has_forbidden_input(result):
            return False

        return self.is_rolled_back(result)

    def _previous_mode(self, state: Mapping[str, Any]) -> str:
        candidates = (
            state.get("current_mode"),
            state.get("mode"),
            state.get("status"),
            state.get("pilot_status"),
            state.get("admission_status"),
        )
        for value in candidates:
            safe = str(value or "").strip()
            if safe:
                return safe

        integration_status = state.get("integration_status")
        if isinstance(integration_status, Mapping):
            safe = str(integration_status.get("mode") or "").strip()
            if safe:
                return safe
        return "unknown"

    def _state_summary(
        self,
        state: Mapping[str, Any],
        previous_mode: str,
        has_forbidden: bool,
    ) -> Dict[str, Any]:
        keys = sorted(
            str(key)
            for key in state.keys()
            if str(key) not in self.forbidden_inputs
        )
        return {
            "runtime_id": str(state.get("runtime_id") or ""),
            "chunk_index": self._safe_int(state.get("chunk_index")),
            "previous_mode": previous_mode,
            "had_admission": bool(
                state.get("admission_status") or state.get("admitted")
            ),
            "had_execution": bool(
                state.get("execution_started") or state.get("execution_allowed")
            ),
            "keys": keys,
            "has_forbidden_inputs": has_forbidden,
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
    def _safe_reason(value: Optional[Any], fallback: str) -> str:
        reason = str(value or "").strip()
        if not reason:
            return fallback
        return reason[:120]


__all__ = ["RealRuntimeRecoveryPilotRollbackController"]
