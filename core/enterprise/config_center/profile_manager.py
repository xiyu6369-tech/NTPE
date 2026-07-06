from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


class ProfileManager:
    DEFAULT_PROFILE = {
        "enterprise": {
            "enabled": True,
            "environment": "development",
            "profile": "default",
            "config_version": "1.2",
        },
        "runtime": {"mode": "compatible", "preserve_legacy": True},
        "translation": {"engine": "existing", "quality_gate": "preserve"},
        "platform": {"deployment": "local-workstation", "audit": True},
    }

    ENVIRONMENT_OVERRIDES = {
        "development": {"enterprise": {"environment": "development"}},
        "staging": {"enterprise": {"environment": "staging", "profile": "staging"}},
        "production": {"enterprise": {"environment": "production", "profile": "production"}},
    }

    def default_profile(self) -> Dict[str, Any]:
        return deepcopy(self.DEFAULT_PROFILE)

    def for_environment(self, environment: str) -> Dict[str, Any]:
        config = self.default_profile()
        return _deep_merge(config, self.ENVIRONMENT_OVERRIDES.get(environment, {}))


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result
