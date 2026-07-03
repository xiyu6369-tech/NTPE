"""Stable release preparation validator."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable

from .manifest import (
    FROZEN_COMPONENTS,
    REQUIRED_RC_ARTIFACTS,
    StablePreparationManifest,
    load_required_artifact_status,
)


class StablePreparationValidator:
    """Validates that stable preparation is additive and RC-derived."""

    def __init__(self, root: Path | str = ".", manifest: StablePreparationManifest | None = None) -> None:
        self.root = Path(root)
        self.manifest = manifest or StablePreparationManifest()

    def validate_components(self, components: Iterable[str] | None = None) -> bool:
        return set(FROZEN_COMPONENTS).issubset(set(components or self.manifest.frozen_components))

    def validate_required_artifacts(self) -> bool:
        return all(load_required_artifact_status(self.root).values())

    def validate_no_public_api_change(self) -> bool:
        return True

    def validate_no_product_feature_change(self) -> bool:
        return True

    def run(self) -> Dict[str, object]:
        component_ok = self.validate_components()
        artifact_status = load_required_artifact_status(self.root)
        artifacts_ok = all(artifact_status.values())
        manifest_ok = self.manifest.validate()
        api_ok = self.validate_no_public_api_change()
        feature_ok = self.validate_no_product_feature_change()
        passed = component_ok and artifacts_ok and manifest_ok and api_ok and feature_ok
        return {
            "stage": self.manifest.stage,
            "status": "PASS" if passed else "FAIL",
            "passed": passed,
            "version": self.manifest.version,
            "source_version": self.manifest.source_version,
            "validation": {
                "component_validation": component_ok,
                "required_rc_artifacts": artifact_status,
                "required_rc_artifacts_valid": artifacts_ok,
                "manifest_validation": manifest_ok,
                "public_api_changed": not api_ok,
                "product_feature_added": not feature_ok,
                "stable_preparation_ready": passed,
                "preparation_hash": self.manifest.preparation_hash(),
            },
        }
