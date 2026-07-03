"""Distribution package models for NTPE Stage-14.4."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from .package_errors import PackageBuildError

VALID_DISTRIBUTION_KINDS = ("full", "increment", "portable", "wheel", "source", "release_bundle")


@dataclass
class DistributionPackage:
    """Describes one generated or planned release distribution artifact."""

    kind: str
    name: str
    path: str
    profile: str = "beta"
    includes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> Dict[str, Any]:
        errors: List[str] = []
        if self.kind not in VALID_DISTRIBUTION_KINDS:
            errors.append(f"invalid kind: {self.kind}")
        if not self.name:
            errors.append("missing name")
        if not self.path:
            errors.append("missing path")
        if not self.profile:
            errors.append("missing profile")
        return {"valid": not errors, "errors": errors, "kind": self.kind, "name": self.name}

    def to_dict(self) -> Dict[str, Any]:
        validation = self.validate()
        return {
            "kind": self.kind,
            "name": self.name,
            "path": self.path,
            "profile": self.profile,
            "includes": list(self.includes),
            "metadata": dict(self.metadata),
            "validation": validation,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "DistributionPackage":
        return cls(
            kind=payload["kind"],
            name=payload["name"],
            path=payload["path"],
            profile=payload.get("profile", "beta"),
            includes=list(payload.get("includes", [])),
            metadata=dict(payload.get("metadata", {})),
        )


def ensure_distribution_package(package: DistributionPackage) -> DistributionPackage:
    validation = package.validate()
    if not validation["valid"]:
        raise PackageBuildError("invalid distribution package: " + ", ".join(validation["errors"]))
    return package
