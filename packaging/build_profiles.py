"""Build profile registry for NTPE Stage-14.3."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .build_profile import BuildProfile
from .package_errors import PackageBuildError


DEFAULT_PROFILE_ORDER = ("development", "beta", "rc", "production")


def default_build_profiles() -> List[BuildProfile]:
    """Return the standard NTPE release profile set."""
    return [
        BuildProfile(
            name="development",
            version_suffix="dev",
            debug=True,
            optimize=False,
            include_tests=True,
            include_docs=True,
            include_reports=True,
            include_source=True,
            include_web_ui=True,
            artifact_kinds=["full", "increment", "source"],
            metadata={"audience": "developers", "stability": "development"},
        ),
        BuildProfile(
            name="beta",
            version_suffix="beta",
            debug=False,
            optimize=False,
            include_tests=True,
            include_docs=True,
            include_reports=True,
            include_source=True,
            include_web_ui=True,
            artifact_kinds=["full", "increment", "portable", "source"],
            metadata={"audience": "beta-testers", "stability": "beta"},
        ),
        BuildProfile(
            name="rc",
            version_suffix="rc",
            debug=False,
            optimize=True,
            include_tests=True,
            include_docs=True,
            include_reports=True,
            include_source=True,
            include_web_ui=True,
            artifact_kinds=["full", "increment", "portable", "wheel", "source"],
            metadata={"audience": "release-candidate", "stability": "rc"},
        ),
        BuildProfile(
            name="production",
            version_suffix="stable",
            debug=False,
            optimize=True,
            include_tests=False,
            include_docs=True,
            include_reports=True,
            include_source=True,
            include_web_ui=True,
            artifact_kinds=["full", "portable", "wheel", "source"],
            metadata={"audience": "end-users", "stability": "production"},
        ),
    ]


@dataclass
class BuildProfileRegistry:
    """Registry for selecting and exporting release build profiles."""

    profiles: Dict[str, BuildProfile] = field(default_factory=dict)

    @classmethod
    def default(cls) -> "BuildProfileRegistry":
        registry = cls()
        for profile in default_build_profiles():
            registry.register(profile)
        return registry

    def register(self, profile: BuildProfile) -> BuildProfile:
        validation = profile.validate()
        if not validation["valid"]:
            raise PackageBuildError("invalid build profile: " + ", ".join(validation["errors"]))
        self.profiles[profile.name] = profile
        return profile

    def get(self, name: str) -> Optional[BuildProfile]:
        return self.profiles.get(name)

    def require(self, name: str) -> BuildProfile:
        profile = self.get(name)
        if profile is None:
            raise PackageBuildError(f"unknown build profile: {name}")
        return profile

    def names(self) -> List[str]:
        return [name for name in DEFAULT_PROFILE_ORDER if name in self.profiles] + [
            name for name in self.profiles if name not in DEFAULT_PROFILE_ORDER
        ]

    def to_list(self) -> List[Dict[str, Any]]:
        return [self.profiles[name].to_dict() for name in self.names()]

    def validate(self, required: Iterable[str] = DEFAULT_PROFILE_ORDER) -> Dict[str, Any]:
        missing = [name for name in required if name not in self.profiles]
        invalid = [name for name, profile in self.profiles.items() if not profile.validate()["valid"]]
        return {
            "valid": not missing and not invalid,
            "count": len(self.profiles),
            "profiles": self.names(),
            "missing": missing,
            "invalid": invalid,
        }

    def write(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "stage": "Stage-14.3",
            "profile_count": len(self.profiles),
            "profiles": self.to_list(),
            "validation": self.validate(),
            "compatibility": {
                "uses_stage_14_2_release_manifest": True,
                "additive_only": True,
                "frozen_api_safe": True,
            },
        }
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return target


def build_profile_manifest(project_root: str | Path, release_root: str | Path | None = None) -> Dict[str, Any]:
    root = Path(project_root)
    if not root.exists():
        raise PackageBuildError(f"project root does not exist: {root}")
    release = Path(release_root or root / "release")
    (release / "manifests").mkdir(parents=True, exist_ok=True)
    registry = BuildProfileRegistry.default()
    path = registry.write(release / "manifests" / "Build_Profiles_Stage_14_3.json")
    return {"path": str(path), "validation": registry.validate(), "profiles": registry.to_list()}


def load_build_profiles(path: str | Path) -> Dict[str, Any]:
    profile_path = Path(path)
    if not profile_path.exists():
        raise PackageBuildError(f"build profile manifest does not exist: {profile_path}")
    return json.loads(profile_path.read_text(encoding="utf-8"))
