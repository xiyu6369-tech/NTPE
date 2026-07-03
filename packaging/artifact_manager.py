"""Artifact registry for NTPE Stage-14.1 packaging core."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .package_errors import ArtifactError


@dataclass(frozen=True)
class Artifact:
    name: str
    kind: str
    path: str
    required: bool = True

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "kind": self.kind,
            "path": self.path,
            "required": self.required,
        }


@dataclass
class ArtifactManager:
    """Small in-memory artifact registry used by release packaging."""

    artifacts: Dict[str, Artifact] = field(default_factory=dict)

    def register(self, name: str, kind: str, path: str | Path, required: bool = True) -> Artifact:
        if not name or not kind:
            raise ArtifactError("artifact name and kind are required")
        artifact = Artifact(name=name, kind=kind, path=str(path), required=required)
        self.artifacts[name] = artifact
        return artifact

    def get(self, name: str) -> Optional[Artifact]:
        return self.artifacts.get(name)

    def list(self) -> List[Dict[str, object]]:
        return [artifact.to_dict() for artifact in self.artifacts.values()]

    def validate(self) -> Dict[str, object]:
        missing = [
            artifact.name
            for artifact in self.artifacts.values()
            if artifact.required and not Path(artifact.path).exists()
        ]
        return {"valid": not missing, "count": len(self.artifacts), "missing": missing}
