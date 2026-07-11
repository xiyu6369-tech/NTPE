
from __future__ import annotations

from typing import Any, Callable, Dict, Mapping, Optional

from .runtime_recovery_hook_adapter import RuntimeRecoveryHookAdapter
from .recovery_outcome_guard import RecoveryOutcomeGuard
from .recovery_result_bundle import RecoveryResultBundle


Handler = Callable[[str, Mapping[str, Any]], Mapping[str, Any]]
RebuildCallback = Callable[[], Any]
SleepCallback = Callable[[int], Any]


class RecoveryFlowIntegration:
    """Compose hook, retry harness, outcome guard, and result bundle.

    This integration remains isolated and callback-driven. It does not import
    or modify Provider Runtime, Translation Runtime, launcher code, HTTP
    clients, or API keys.
    """

    version = "TE-v4.1"
    stage = "4.1.5"
    name = "recovery_flow_integration"

    def __init__(self) -> None:
        self.hook = RuntimeRecoveryHookAdapter()
        self.guard = RecoveryOutcomeGuard()
        self.bundle = RecoveryResultBundle()

    def run(
        self,
        request: Optional[Mapping[str, Any]] = None,
        handler: Optional[Handler] = None,
        rebuild_callback: Optional[RebuildCallback] = None,
        sleep_callback: Optional[SleepCallback] = None,
    ) -> Dict[str, Any]:
        data = dict(request or {})
        source_text = str(data.get("source_text") or "")
        translated_holder: Dict[str, str] = {"text": ""}

        def wrapped_handler(text: str, context: Mapping[str, Any]) -> Mapping[str, Any]:
            raw = dict(handler(text, context) or {}) if callable(handler) else {}
            translated = str(raw.get("translated_text") or "")
            if translated:
                translated_holder["text"] += translated
            return raw

        hook_result = self.hook.invoke(
            data,
            handler=wrapped_handler if callable(handler) else None,
            rebuild_callback=rebuild_callback,
            sleep_callback=sleep_callback,
        )

        if hook_result.get("blocked") is True:
            return {
                "status": "flow_blocked",
                "accepted": False,
                "stage": self.stage,
                "runtime_id": str(data.get("runtime_id") or ""),
                "hook_result": hook_result,
                "guard_result": {},
                "bundle": {},
                "source_text_retained": False,
                "translated_text_retained": False,
                "integration_status": self._integration_status(),
                "metadata": self._metadata(),
            }

        guard_result = self.guard.evaluate(
            source_text,
            translated_holder["text"],
            hook_result.get("harness_result"),
            {
                "min_length_ratio": data.get("min_length_ratio", 0.35),
                "max_length_ratio": data.get("max_length_ratio", 2.5),
                "max_hangul_residue": data.get("max_hangul_residue", 0),
                "max_duplicate_lines": data.get("max_duplicate_lines", 0),
            },
        )

        bundle = self.bundle.build(
            str(data.get("runtime_id") or ""),
            hook_result,
            guard_result,
            {
                "profile": data.get("profile", "unknown"),
                "flow_stage": self.stage,
            },
        )

        return {
            "status": (
                "flow_completed"
                if bundle.get("accepted") is True
                else "flow_rejected"
            ),
            "accepted": bundle.get("accepted") is True,
            "stage": self.stage,
            "runtime_id": str(data.get("runtime_id") or ""),
            "hook_result": hook_result,
            "guard_result": guard_result,
            "bundle": bundle,
            "source_text_retained": False,
            "translated_text_retained": False,
            "integration_status": self._integration_status(),
            "metadata": self._metadata(),
        }

    def validate_result(self, result: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(result, Mapping):
            return False

        required = {
            "status",
            "accepted",
            "stage",
            "runtime_id",
            "hook_result",
            "guard_result",
            "bundle",
            "source_text_retained",
            "translated_text_retained",
            "integration_status",
            "metadata",
        }
        if not required.issubset(result):
            return False
        if result.get("stage") != self.stage:
            return False
        if result.get("source_text_retained") is not False:
            return False
        if result.get("translated_text_retained") is not False:
            return False

        integration = result.get("integration_status")
        if not isinstance(integration, Mapping):
            return False
        for key in (
            "provider_runtime_modified",
            "translation_runtime_modified",
            "launcher_modified",
            "http_called",
            "api_key_accessed",
            "real_translation_runtime_used",
        ):
            if integration.get(key) is not False:
                return False

        if result.get("status") == "flow_blocked":
            return (
                result.get("accepted") is False
                and result.get("guard_result") == {}
                and result.get("bundle") == {}
                and self.hook.validate_result(result.get("hook_result"))
            )

        if result.get("status") not in {"flow_completed", "flow_rejected"}:
            return False
        if not self.hook.validate_result(result.get("hook_result")):
            return False
        if not self.guard.validate_result(result.get("guard_result")):
            return False
        if not self.bundle.validate_bundle(result.get("bundle")):
            return False

        expected = result.get("status") == "flow_completed"
        if result.get("accepted") is not expected:
            return False
        return True

    @staticmethod
    def _integration_status() -> Dict[str, Any]:
        return {
            "mode": "isolated_recovery_flow",
            "provider_runtime_modified": False,
            "translation_runtime_modified": False,
            "launcher_modified": False,
            "http_called": False,
            "api_key_accessed": False,
            "real_translation_runtime_used": False,
        }

    def _metadata(self) -> Dict[str, Any]:
        return {
            "flow": self.name,
            "version": self.version,
            "stage": self.stage,
            "components": [
                "RuntimeRecoveryHookAdapter",
                "AdaptiveRetryExecutionHarness",
                "RecoveryOutcomeGuard",
                "RecoveryResultBundle",
            ],
        }


__all__ = ["RecoveryFlowIntegration"]
