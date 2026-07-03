"""Release dependency manifest model for NTPE Stage-14.2."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class ReleaseDependency:
    name: str
    kind: str = "internal"
    required: bool = True
    version: str = "frozen"

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "kind": self.kind,
            "required": self.required,
            "version": self.version,
        }


@dataclass
class DependencyManifest:
    dependencies: List[ReleaseDependency] = field(default_factory=list)

    @classmethod
    def default_beta_dependencies(cls) -> "DependencyManifest":
        return cls([
            ReleaseDependency("python", "runtime", True, ">=3.10"),
            ReleaseDependency("foundation", "internal", True, "v1.0-frozen"),
            ReleaseDependency("runtime_api", "internal", True, "stage-11.8-frozen"),
            ReleaseDependency("external_api", "internal", True, "stage-12.8-frozen"),
            ReleaseDependency("web_ui", "internal", True, "stage-13.8-frozen"),
        ])

    def add(self, dependency: ReleaseDependency) -> None:
        self.dependencies.append(dependency)

    def to_list(self) -> List[Dict[str, object]]:
        return [dependency.to_dict() for dependency in self.dependencies]

    def validate(self) -> Dict[str, object]:
        missing_required = [dep.name for dep in self.dependencies if dep.required and not dep.name]
        return {
            "valid": not missing_required and bool(self.dependencies),
            "count": len(self.dependencies),
            "missing_required": missing_required,
        }
