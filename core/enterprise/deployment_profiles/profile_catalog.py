from __future__ import annotations

from typing import Dict, Iterable, List

from .profile import DeploymentProfile


class DeploymentProfileCatalog:
    """In-memory catalog of supported enterprise deployment profiles."""

    def __init__(self) -> None:
        self._profiles: Dict[str, DeploymentProfile] = {}
        for profile in self._default_profiles():
            self.register(profile)

    def _default_profiles(self) -> Iterable[DeploymentProfile]:
        return [
            DeploymentProfile(
                name="local-workstation",
                target="local-workstation",
                environment="development",
                enabled_capabilities=["single_node", "local_config", "manual_validation"],
                config_overrides={"enterprise": {"deployment_profile": "local-workstation"}},
            ),
            DeploymentProfile(
                name="team-shared-runtime",
                target="team-shared-runtime",
                environment="staging",
                enabled_capabilities=["shared_config", "audit_export", "rollback_plan"],
                config_overrides={"enterprise": {"deployment_profile": "team-shared-runtime"}},
            ),
            DeploymentProfile(
                name="enterprise-controlled-host",
                target="enterprise-controlled-host",
                environment="production",
                enabled_capabilities=["controlled_host", "audit_export", "config_lock", "rollback_plan"],
                config_overrides={"enterprise": {"deployment_profile": "enterprise-controlled-host"}},
            ),
        ]

    def register(self, profile: DeploymentProfile) -> None:
        if not profile.name:
            raise ValueError("Deployment profile name is required")
        self._profiles[profile.name] = profile

    def get(self, name: str) -> DeploymentProfile:
        try:
            return self._profiles[name]
        except KeyError as exc:
            raise KeyError(f"Unknown deployment profile: {name}") from exc

    def names(self) -> List[str]:
        return sorted(self._profiles)

    def all(self) -> List[DeploymentProfile]:
        return [self._profiles[name] for name in self.names()]
