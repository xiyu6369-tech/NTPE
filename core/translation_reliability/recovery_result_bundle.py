
from __future__ import annotations

from typing import Any, Dict, Mapping, Optional


class RecoveryResultBundle:
    """Build a single safe bundle from recovery and outcome-guard results."""

    version = "TE-v4.1"
    stage = "4.1.4"
    name = "recovery_result_bundle"

    def build(
        self,
        runtime_id: Optional[str],
        hook_result: Optional[Mapping[str, Any]],
        guard_result: Optional[Mapping[str, Any]],
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        hook = dict(hook_result or {})
        guard = dict(guard_result or {})
        safe_metadata = self._safe_metadata(metadata)

        accepted = (
            hook.get("status") == "recovery_completed"
            and hook.get("allowed") is True
            and hook.get("blocked") is False
            and guard.get("accepted") is True
            and guard.get("status") == "accepted"
        )

        status = "recovery_accepted" if accepted else "recovery_rejected"

        return {
            "status": status,
            "accepted": accepted,
            "stage": self.stage,
            "runtime_id": str(runtime_id or hook.get("runtime_id") or ""),
            "recovery_summary": dict(hook.get("recovery_summary") or {}),
            "guard_summary": {
                "accepted": guard.get("accepted") is True,
                "status": str(guard.get("status") or "unknown"),
                "issues": list(guard.get("issues") or []),
                "metrics": dict(guard.get("metrics") or {}),
            },
            "hook_status": str(hook.get("status") or "unknown"),
            "final_outcome": str(
                (hook.get("recovery_summary") or {}).get("final_outcome")
                or "unknown"
            ),
            "source_text_retained": False,
            "translated_text_retained": False,
            "integration_status": {
                "mode": "bundle_only",
                "runtime_modified": False,
                "provider_runtime_modified": False,
                "launcher_modified": False,
                "http_called": False,
                "api_key_accessed": False,
                "real_translation_runtime_used": False,
            },
            "metadata": {
                "bundle": self.name,
                "version": self.version,
                "stage": self.stage,
                **safe_metadata,
            },
        }

    def validate_bundle(self, bundle: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(bundle, Mapping):
            return False

        required = {
            "status",
            "accepted",
            "stage",
            "runtime_id",
            "recovery_summary",
            "guard_summary",
            "hook_status",
            "final_outcome",
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
            "recovery_accepted",
            "recovery_rejected",
        }:
            return False
        if bundle.get("accepted") is True and bundle.get("status") != "recovery_accepted":
            return False
        if bundle.get("accepted") is False and bundle.get("status") != "recovery_rejected":
            return False
        if bundle.get("source_text_retained") is not False:
            return False
        if bundle.get("translated_text_retained") is not False:
            return False

        guard = bundle.get("guard_summary")
        if not isinstance(guard, Mapping):
            return False
        if not isinstance(guard.get("issues"), list):
            return False

        integration = bundle.get("integration_status")
        if not isinstance(integration, Mapping):
            return False

        for key in (
            "runtime_modified",
            "provider_runtime_modified",
            "launcher_modified",
            "http_called",
            "api_key_accessed",
            "real_translation_runtime_used",
        ):
            if integration.get(key) is not False:
                return False

        if not isinstance(bundle.get("metadata"), Mapping):
            return False
        return True

    @staticmethod
    def _safe_metadata(metadata: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
        if not isinstance(metadata, Mapping):
            return {}
        blocked = {
            "source_text",
            "translated_text",
            "text",
            "chunks",
            "api_key",
            "provider_client",
        }
        return {
            str(key): value
            for key, value in metadata.items()
            if str(key) not in blocked
        }


__all__ = ["RecoveryResultBundle"]
