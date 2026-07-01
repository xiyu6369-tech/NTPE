"""Foundation-08.8 Knowledge package validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

SUPPORTED_PACKAGE_VERSION = "foundation-08.8"
SUPPORTED_SCHEMA = "ntpe.knowledge.package.v1"


@dataclass
class KnowledgePackageValidationResult:
    valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.valid = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def to_dict(self) -> Dict[str, Any]:
        return {"valid": self.valid, "errors": list(self.errors), "warnings": list(self.warnings)}


class KnowledgePackageValidator:
    """Validate portable Knowledge Layer packages before import."""

    version = SUPPORTED_PACKAGE_VERSION

    def validate(self, package: Dict[str, Any]) -> KnowledgePackageValidationResult:
        result = KnowledgePackageValidationResult()
        if not isinstance(package, dict):
            result.add_error("package must be a dictionary")
            return result

        manifest = package.get("manifest")
        if not isinstance(manifest, dict):
            result.add_error("manifest is required")
            return result

        if manifest.get("schema") != SUPPORTED_SCHEMA:
            result.add_warning("package schema differs from current schema")

        if not manifest.get("version"):
            result.add_error("manifest.version is required")

        items = package.get("items", [])
        if not isinstance(items, list):
            result.add_error("items must be a list")
        else:
            for index, item in enumerate(items):
                if not isinstance(item, dict):
                    result.add_error(f"items[{index}] must be a dictionary")
                    continue
                if not item.get("key"):
                    result.add_error(f"items[{index}].key is required")
                if not item.get("domain"):
                    result.add_error(f"items[{index}].domain is required")

        snapshots = package.get("snapshots", [])
        if snapshots is not None and not isinstance(snapshots, list):
            result.add_error("snapshots must be a list")

        return result

    def ensure_valid(self, package: Dict[str, Any]) -> KnowledgePackageValidationResult:
        result = self.validate(package)
        if not result.valid:
            raise ValueError("Invalid knowledge package: " + "; ".join(result.errors))
        return result

    def compatible(self, package: Dict[str, Any]) -> bool:
        result = self.validate(package)
        return result.valid


__all__ = [
    "KnowledgePackageValidationResult",
    "KnowledgePackageValidator",
    "SUPPORTED_PACKAGE_VERSION",
    "SUPPORTED_SCHEMA",
]
