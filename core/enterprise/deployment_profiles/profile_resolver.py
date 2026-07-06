from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from core.enterprise.config_center import EnterpriseConfigCenter

from .profile import DeploymentProfile
from .profile_catalog import DeploymentProfileCatalog


def _deep_merge(base: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(base)
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


class DeploymentProfileResolver:
    """Resolves a profile into an Enterprise Configuration Center payload."""

    stage = "Stage-18.3"
    name = "Enterprise Deployment Profiles"

    def __init__(self, config_center: EnterpriseConfigCenter | None = None, catalog: DeploymentProfileCatalog | None = None) -> None:
        self.config_center = config_center or EnterpriseConfigCenter()
        self.catalog = catalog or DeploymentProfileCatalog()

    def resolve(self, profile_name: str) -> Dict[str, Any]:
        profile = self.catalog.get(profile_name)
        config = self.config_center.load(environment=profile.environment)
        resolved = _deep_merge(config, profile.config_overrides)
        resolved.setdefault("enterprise", {})
        resolved["enterprise"].update({
            "deployment_profile": profile.name,
            "deployment_target": profile.target,
            "deployment_mode": profile.mode,
            "capabilities": list(profile.enabled_capabilities),
        })
        self.config_center.validator.validate(resolved)
        return resolved

    def describe(self, profile_name: str) -> Dict[str, Any]:
        profile = self.catalog.get(profile_name)
        return {
            "stage": self.stage,
            "name": self.name,
            "profile": profile.to_dict(),
            "resolved_environment": profile.environment,
        }
