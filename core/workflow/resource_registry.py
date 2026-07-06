# =====================================================
# NTPE 1.2 Professional
# Stage-17.3 Resource Optimizer
# =====================================================

from __future__ import annotations

from typing import Dict, Iterable, List

from .resource_profile import ResourceProfile


class ResourceProfileRegistry:
    def __init__(self, profiles: Iterable[ResourceProfile] | None = None) -> None:
        self._profiles: Dict[str, ResourceProfile] = {}
        for profile in profiles or []:
            self.register(profile)

    def register(self, profile: ResourceProfile) -> None:
        self._profiles[f"{profile.provider}:{profile.model}"] = profile

    def get(self, provider: str, model: str = "default") -> ResourceProfile | None:
        return self._profiles.get(f"{provider}:{model}")

    def list(self) -> List[ResourceProfile]:
        return list(self._profiles.values())
