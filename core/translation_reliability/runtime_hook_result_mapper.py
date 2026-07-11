from __future__ import annotations

from typing import Any, Dict, Mapping, Optional


class RuntimeHookResultMapper:
    """Maps shadow hook results into safe runtime-readable recommendations."""

    version = "TE-v4.3"
    stage = "4.3.4"
    name = "runtime_hook_result_mapper"

    forbidden_inputs = {
        "source_text",
        "translated_text",
        "text",
        "chunks",
        "api_key",
        "provider_client",
    }

    def map_result(
        self,
        runtime_id: str,
        hook_result: Optional[Mapping[str, Any]],
        rollback_result: Optional[Mapping[str, Any]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        hook = dict(hook_result or {}) if isinstance(hook_result, Mapping) else {}
        rollback = dict(rollback_result or {}) if isinstance(rollback_result, Mapping) else {}
        shadow = hook.get("shadow_result") if isinstance(hook.get("shadow_result"), Mapping) else {}

        if rollback.get("rolled_back") is True:
            status = "shadow_rolled_back"
        elif hook.get("status") == "shadow_hook_completed" and shadow.get("recovery_recommended") is True:
            status = "shadow_recommendation_available"
        elif hook.get("status") == "shadow_hook_completed":
            status = "shadow_no_action"
        else:
            status = "shadow_hook_failed"

        return {
            "status": status,
            "stage": self.stage,
            "runtime_id": str(runtime_id or hook.get("runtime_id") or ""),
            "recovery_recommended": status == "shadow_recommendation_available",
            "recommended_action": str(shadow.get("recommended_action") or ""),
            "original_runtime_result_unchanged": True,
            "result_replacement_allowed": False,
            "provider_fallback_executed": False,
            "real_provider_request_executed": False,
            "rollback_available": True,
            "source_text_retained": False,
            "translated_text_retained": False,
            "hook_summary": self._hook_summary(hook),
            "rollback_summary": self._rollback_summary(rollback),
            "metadata": self._sanitize(metadata or {}),
        }

    def should_replace_runtime_result(self, mapping: Optional[Mapping[str, Any]]) -> bool:
        return False

    def validate_mapping(self, mapping: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(mapping, Mapping):
            return False
        required = {
            "status",
            "stage",
            "runtime_id",
            "recovery_recommended",
            "recommended_action",
            "original_runtime_result_unchanged",
            "result_replacement_allowed",
            "provider_fallback_executed",
            "real_provider_request_executed",
            "rollback_available",
            "source_text_retained",
            "translated_text_retained",
            "hook_summary",
            "rollback_summary",
            "metadata",
        }
        if not required.issubset(mapping):
            return False
        if mapping.get("stage") != self.stage:
            return False
        if mapping.get("status") not in {
            "shadow_recommendation_available",
            "shadow_no_action",
            "shadow_hook_failed",
            "shadow_rolled_back",
        }:
            return False
        if mapping.get("original_runtime_result_unchanged") is not True:
            return False
        for key in (
            "result_replacement_allowed",
            "provider_fallback_executed",
            "real_provider_request_executed",
            "source_text_retained",
            "translated_text_retained",
        ):
            if mapping.get(key) is not False:
                return False
        if mapping.get("rollback_available") is not True:
            return False
        if self._has_forbidden_input(mapping):
            return False
        return self.should_replace_runtime_result(mapping) is False

    def _hook_summary(self, hook: Mapping[str, Any]) -> Dict[str, Any]:
        shadow = hook.get("shadow_result") if isinstance(hook.get("shadow_result"), Mapping) else {}
        return {
            "status": str(hook.get("status") or ""),
            "completed": hook.get("completed") is True,
            "callback_called": hook.get("callback_called") is True,
            "recovery_recommended": shadow.get("recovery_recommended") is True,
            "recommended_action": str(shadow.get("recommended_action") or ""),
        }

    def _rollback_summary(self, rollback: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "rolled_back": rollback.get("rolled_back") is True,
            "status": str(rollback.get("status") or ""),
            "current_mode": str(rollback.get("current_mode") or ""),
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


__all__ = ["RuntimeHookResultMapper"]
