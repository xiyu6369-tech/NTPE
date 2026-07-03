"""Release manifest schema helpers for NTPE Stage-14.2."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List


RELEASE_MANIFEST_REQUIRED_FIELDS = (
    "name",
    "version",
    "stage",
    "profile",
    "components",
    "dependencies",
    "artifacts",
    "compatibility",
)


@dataclass(frozen=True)
class ManifestSchema:
    """Small declarative schema validator for release manifests.

    This intentionally stays dependency-free so packaging remains portable and
    usable in freeze tests without requiring jsonschema or build backends.
    """

    required_fields: Iterable[str] = field(default_factory=lambda: RELEASE_MANIFEST_REQUIRED_FIELDS)

    def validate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        missing: List[str] = [field for field in self.required_fields if field not in payload]
        type_errors: List[str] = []
        if "components" in payload and not isinstance(payload["components"], list):
            type_errors.append("components must be a list")
        if "dependencies" in payload and not isinstance(payload["dependencies"], list):
            type_errors.append("dependencies must be a list")
        if "artifacts" in payload and not isinstance(payload["artifacts"], list):
            type_errors.append("artifacts must be a list")
        if "compatibility" in payload and not isinstance(payload["compatibility"], dict):
            type_errors.append("compatibility must be a dict")
        return {
            "valid": not missing and not type_errors,
            "missing": missing,
            "type_errors": type_errors,
            "required_fields": list(self.required_fields),
        }
