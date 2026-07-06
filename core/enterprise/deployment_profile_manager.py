# =====================================================
# NTPE 1.2 Professional
# Stage-18.3 Enterprise Deployment Profiles
# =====================================================

from __future__ import annotations

from typing import Any, Dict, List

from .deployment_profiles import DeploymentProfile, DeploymentProfileCatalog, DeploymentProfileResolver
from .deployment_profiles.profile_audit import build_profile_audit


class EnterpriseDeploymentProfileManager:
    """Enterprise deployment profile facade.

    Additive Stage-18.3 layer. It resolves deployment profiles against the
    Stage-18.2 configuration center without modifying frozen runtime modules.
    """

    stage = "Stage-18.3"
    name = "Enterprise Deployment Profiles"

    def __init__(self) -> None:
        self.catalog = DeploymentProfileCatalog()
        self.resolver = DeploymentProfileResolver(catalog=self.catalog)

    def available_profiles(self) -> List[str]:
        return self.catalog.names()

    def register_profile(self, profile: DeploymentProfile) -> None:
        self.catalog.register(profile)

    def resolve_profile(self, name: str) -> Dict[str, Any]:
        return self.resolver.resolve(name)

    def audit_profile(self, name: str) -> Dict[str, Any]:
        resolved = self.resolve_profile(name)
        return build_profile_audit(name, resolved, validated=True).to_dict()

    def manifest(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "name": self.name,
            "status": "active",
            "profiles": self.available_profiles(),
            "compatibility": [
                "Additive deployment profile layer only.",
                "Stage-18.2 configuration center remains canonical.",
                "No frozen Foundation or LTS modules are modified.",
            ],
        }
