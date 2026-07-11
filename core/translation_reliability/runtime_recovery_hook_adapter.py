
from __future__ import annotations

from typing import Any, Callable, Dict, Mapping, Optional

from .adaptive_retry_execution_harness import AdaptiveRetryExecutionHarness


Handler = Callable[[str, Mapping[str, Any]], Mapping[str, Any]]
RebuildCallback = Callable[[], Any]
SleepCallback = Callable[[int], Any]


class RuntimeRecoveryHookAdapter:
    """Opt-in adapter around AdaptiveRetryExecutionHarness.

    The adapter exposes a Runtime-facing contract without importing or
    modifying Translation Runtime. All execution is delegated to injected
    callbacks and remains disabled by default.
    """

    version = "TE-v4.1"
    stage = "4.1.2"
    name = "runtime_recovery_hook_adapter"

    def __init__(self) -> None:
        self.harness = AdaptiveRetryExecutionHarness()

    def invoke(
        self,
        request: Optional[Mapping[str, Any]] = None,
        handler: Optional[Handler] = None,
        rebuild_callback: Optional[RebuildCallback] = None,
        sleep_callback: Optional[SleepCallback] = None,
    ) -> Dict[str, Any]:
        data = dict(request or {})
        enabled = data.get("enabled") is True

        if not enabled:
            return self._blocked_result("hook_disabled")

        if str(data.get("caller") or "") != "translation_runtime":
            return self._blocked_result("invalid_caller")

        runtime_id = str(data.get("runtime_id") or "").strip()
        if not runtime_id:
            return self._blocked_result("runtime_id_required")

        source_text = str(data.get("source_text") or "")
        if not source_text:
            return self._blocked_result("source_text_required")

        if not callable(handler):
            return self._blocked_result("handler_required")

        harness_result = self.harness.execute(
            source_text,
            handler,
            {
                "enabled": True,
                "max_attempts": data.get("max_attempts", 5),
                "base_delay_seconds": data.get("base_delay_seconds", 5),
                "max_delay_seconds": data.get("max_delay_seconds", 60),
                "timeout_seconds": data.get("timeout_seconds", 180),
                "max_timeout_seconds": data.get("max_timeout_seconds", 300),
                "chunk_size": data.get("chunk_size", len(source_text) or 600),
                "min_chunk_size": data.get("min_chunk_size", 200),
                "max_chunk_size": data.get("max_chunk_size", 1200),
            },
            rebuild_callback=rebuild_callback,
            sleep_callback=sleep_callback,
        )

        status = (
            "recovery_completed"
            if harness_result.get("success") is True
            else "recovery_failed"
        )

        return {
            "status": status,
            "allowed": True,
            "blocked": False,
            "stage": self.stage,
            "runtime_id": runtime_id,
            "hook_mode": "isolated_recovery",
            "harness_result": harness_result,
            "recovery_summary": {
                "success": harness_result.get("success") is True,
                "attempts_used": int(harness_result.get("attempts_used", 0) or 0),
                "rebuild_count": int(harness_result.get("rebuild_count", 0) or 0),
                "split_count": int(harness_result.get("split_count", 0) or 0),
                "final_outcome": str(
                    harness_result.get("final_outcome") or "unknown_failure"
                ),
            },
            "source_text_retained": False,
            "translated_text_retained": False,
            "integration_status": {
                "runtime_hook_invoked": True,
                "runtime_modified": False,
                "provider_runtime_modified": False,
                "launcher_modified": False,
                "http_client_imported": False,
                "api_key_accessed": False,
                "real_translation_runtime_used": False,
                "handler_injected": True,
            },
            "metadata": {
                "adapter": self.name,
                "version": self.version,
                "caller": "translation_runtime",
                "request_keys": sorted(
                    key
                    for key in data.keys()
                    if key
                    not in {
                        "source_text",
                        "text",
                        "translated_text",
                        "api_key",
                        "provider_client",
                    }
                ),
            },
        }

    def validate_result(self, result: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(result, Mapping):
            return False

        required = {
            "status",
            "allowed",
            "blocked",
            "stage",
            "runtime_id",
            "hook_mode",
            "harness_result",
            "recovery_summary",
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
            "runtime_modified",
            "provider_runtime_modified",
            "launcher_modified",
            "http_client_imported",
            "api_key_accessed",
            "real_translation_runtime_used",
        ):
            if integration.get(key) is not False:
                return False

        if result.get("blocked") is True:
            return (
                result.get("allowed") is False
                and result.get("status") == "blocked"
                and result.get("harness_result") == {}
            )

        if result.get("allowed") is not True:
            return False
        if result.get("status") not in {
            "recovery_completed",
            "recovery_failed",
        }:
            return False
        if result.get("hook_mode") != "isolated_recovery":
            return False
        if not self.harness.validate_result(result.get("harness_result")):
            return False

        return True

    def _blocked_result(self, reason: str) -> Dict[str, Any]:
        return {
            "status": "blocked",
            "allowed": False,
            "blocked": True,
            "stage": self.stage,
            "runtime_id": "",
            "hook_mode": "disabled",
            "reason": reason,
            "harness_result": {},
            "recovery_summary": {
                "success": False,
                "attempts_used": 0,
                "rebuild_count": 0,
                "split_count": 0,
                "final_outcome": "not_started",
            },
            "source_text_retained": False,
            "translated_text_retained": False,
            "integration_status": {
                "runtime_hook_invoked": False,
                "runtime_modified": False,
                "provider_runtime_modified": False,
                "launcher_modified": False,
                "http_client_imported": False,
                "api_key_accessed": False,
                "real_translation_runtime_used": False,
                "handler_injected": False,
            },
            "metadata": {
                "adapter": self.name,
                "version": self.version,
                "caller": "",
                "request_keys": [],
            },
        }


__all__ = ["RuntimeRecoveryHookAdapter"]
