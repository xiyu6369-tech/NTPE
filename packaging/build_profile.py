"""Build profile model for NTPE Stage-14.3."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class BuildProfile:
    """Declarative release build profile.

    Profiles are intentionally data-only so they can be consumed by packaging,
    CI, CLI, REST, or Web UI tooling without coupling to implementation details.
    """

    name: str
    version_suffix: str
    debug: bool = False
    optimize: bool = False
    include_tests: bool = False
    include_docs: bool = True
    include_reports: bool = True
    include_source: bool = True
    include_web_ui: bool = True
    artifact_kinds: List[str] = field(default_factory=lambda: ["full", "increment"])
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version_suffix": self.version_suffix,
            "debug": self.debug,
            "optimize": self.optimize,
            "include_tests": self.include_tests,
            "include_docs": self.include_docs,
            "include_reports": self.include_reports,
            "include_source": self.include_source,
            "include_web_ui": self.include_web_ui,
            "artifact_kinds": list(self.artifact_kinds),
            "metadata": dict(self.metadata),
        }

    def validate(self) -> Dict[str, Any]:
        errors: List[str] = []
        if not self.name:
            errors.append("profile name is required")
        if not self.version_suffix:
            errors.append("version suffix is required")
        if not self.artifact_kinds:
            errors.append("at least one artifact kind is required")
        return {"valid": not errors, "name": self.name, "errors": errors}
