from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class RuntimeIntegrationFeatureFlag:
    """Disabled-by-default resolver for runtime scheduler integration."""

    stage = "3.3.2"
    env_name = "NTPE_RUNTIME_SCHEDULER_INTEGRATION"
    config_key = "runtime_scheduler_integration_enabled"
    enabled_env_values = {"1", "true", "yes", "enabled"}
    safety_boundaries = {
        "provider_runtime": "external",
        "http_client": "forbidden",
        "api_key": "forbidden",
        "launcher_flow": "unchanged",
        "translation_runtime_flow": "unchanged",
    }

    def resolve(self, config: Mapping[str, Any] | None = None, env: Mapping[str, Any] | None = None) -> dict[str, Any]:
        config_data = dict(config or {})
        env_data = dict(env or {})

        if self.config_key in config_data:
            enabled = config_data.get(self.config_key) is True
            return self._state(
                enabled=enabled,
                source="config",
                reason="config_enabled" if enabled else "config_disabled",
                metadata={"config_key": self.config_key},
            )

        env_value = env_data.get(self.env_name)
        if env_value is not None:
            normalized = str(env_value).strip().lower()
            enabled = normalized in self.enabled_env_values
            return self._state(
                enabled=enabled,
                source="env",
                reason="env_enabled" if enabled else "env_invalid_or_disabled",
                metadata={"env_name": self.env_name, "env_value": str(env_value)},
            )

        return self._state(
            enabled=False,
            source="default",
            reason="default_disabled",
            metadata={"disabled_by_default": True},
        )

    def is_enabled(self, flag_state: Mapping[str, Any] | None) -> bool:
        state = dict(flag_state or {})
        return state.get("enabled") is True

    def validate_flag_state(self, flag_state: Mapping[str, Any] | None) -> dict[str, Any]:
        state = dict(flag_state or {})
        errors: list[str] = []

        if not isinstance(state.get("enabled"), bool):
            errors.append("enabled boolean is required")
        if state.get("source") not in {"default", "config", "env"}:
            errors.append("source must be default, config, or env")
        if not isinstance(state.get("reason"), str) or not state.get("reason"):
            errors.append("reason is required")
        if state.get("stage") != self.stage:
            errors.append("stage must be 3.3.2")

        boundaries = state.get("safety_boundaries")
        if not isinstance(boundaries, Mapping):
            errors.append("safety_boundaries mapping is required")
            boundaries = {}
        for key, expected in self.safety_boundaries.items():
            if boundaries.get(key) != expected:
                errors.append(f"{key} boundary must be {expected}")

        if not isinstance(state.get("metadata"), Mapping):
            errors.append("metadata mapping is required")

        return {"valid": not errors, "errors": errors}

    def _state(self, enabled: bool, source: str, reason: str, metadata: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "enabled": enabled,
            "source": source,
            "reason": reason,
            "stage": self.stage,
            "safety_boundaries": dict(self.safety_boundaries),
            "metadata": {
                "feature_flag": "runtime_scheduler_integration",
                **dict(metadata),
            },
        }


__all__ = ["RuntimeIntegrationFeatureFlag"]
