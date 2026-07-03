"""Release component manifest model for NTPE Stage-14.2."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class ReleaseComponent:
    name: str
    stage: str
    status: str = "frozen"
    public_api: bool = True
    notes: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "stage": self.stage,
            "status": self.status,
            "public_api": self.public_api,
            "notes": self.notes,
        }


@dataclass
class ComponentManifest:
    components: List[ReleaseComponent] = field(default_factory=list)

    @classmethod
    def default_beta_components(cls) -> "ComponentManifest":
        return cls([
            ReleaseComponent("foundation", "Foundation v1.0", "frozen", True),
            ReleaseComponent("cli", "Stage-06", "frozen", True),
            ReleaseComponent("sdk", "Stage-07", "completed", True),
            ReleaseComponent("integration", "Stage-08", "frozen", True),
            ReleaseComponent("workflow", "Stage-09", "frozen", True),
            ReleaseComponent("platform_services", "Stage-10", "frozen", True),
            ReleaseComponent("runtime_api", "Stage-11", "frozen", True),
            ReleaseComponent("external_api", "Stage-12", "frozen", True),
            ReleaseComponent("web_ui", "Stage-13", "frozen", True),
            ReleaseComponent("packaging", "Stage-14.2", "active", True),
        ])

    def add(self, component: ReleaseComponent) -> None:
        self.components.append(component)

    def to_list(self) -> List[Dict[str, object]]:
        return [component.to_dict() for component in self.components]

    def validate(self) -> Dict[str, object]:
        missing_names = [index for index, component in enumerate(self.components) if not component.name]
        duplicate_names = sorted({
            component.name
            for component in self.components
            if sum(1 for item in self.components if item.name == component.name) > 1
        })
        return {
            "valid": not missing_names and not duplicate_names and bool(self.components),
            "count": len(self.components),
            "missing_names": missing_names,
            "duplicate_names": duplicate_names,
        }
