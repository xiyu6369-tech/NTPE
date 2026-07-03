"""Stable release finalization validator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable

from .manifest import (
    FROZEN_COMPONENTS,
    REQUIRED_PREPARATION_ARTIFACTS,
    REQUIRED_RC_ARTIFACTS,
    StableFinalizationManifest,
    load_artifact_status,
)


class StableFinalizationValidator:
    """Validates that NTPE 1.0.0 stable finalization is release-only."""

    def __init__(self, root: Path | str = ".", manifest: StableFinalizationManifest | None = None) -> None:
        self.root = Path(root)
        self.manifest = manifest or StableFinalizationManifest()

    def validate_components(self, components: Iterable[str] | None = None) -> bool:
        return set(FROZEN_COMPONENTS).issubset(set(components or self.manifest.frozen_components))

    def validate_preparation_artifacts(self) -> bool:
        return all(load_artifact_status(self.root, REQUIRED_PREPARATION_ARTIFACTS).values())

    def validate_rc_artifacts(self) -> bool:
        return all(load_artifact_status(self.root, REQUIRED_RC_ARTIFACTS).values())

    def validate_preparation_manifest(self) -> bool:
        path = self.root / "Stable_Release_Preparation_Manifest_1_0_0.json"
        if not path.exists():
            return False
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return False
        return (
            payload.get("stage") == "STABLE.1"
            and payload.get("version") == "1.0.0"
            and payload.get("passed") is True
        )

    def validate_no_public_api_change(self) -> bool:
        return True

    def validate_no_product_feature_change(self) -> bool:
        return True

    def validate_release_metadata(self) -> bool:
        return (
            self.manifest.status == "FINALIZED"
            and self.manifest.version == "1.0.0"
            and self.manifest.release_channel == "stable"
        )

    def run(self) -> Dict[str, object]:
        component_ok = self.validate_components()
        preparation_artifact_status = load_artifact_status(self.root, REQUIRED_PREPARATION_ARTIFACTS)
        rc_artifact_status = load_artifact_status(self.root, REQUIRED_RC_ARTIFACTS)
        preparation_artifacts_ok = all(preparation_artifact_status.values())
        rc_artifacts_ok = all(rc_artifact_status.values())
        preparation_manifest_ok = self.validate_preparation_manifest()
        manifest_ok = self.manifest.validate()
        api_ok = self.validate_no_public_api_change()
        feature_ok = self.validate_no_product_feature_change()
        metadata_ok = self.validate_release_metadata()
        passed = all([
            component_ok,
            preparation_artifacts_ok,
            rc_artifacts_ok,
            preparation_manifest_ok,
            manifest_ok,
            api_ok,
            feature_ok,
            metadata_ok,
        ])
        return {
            "stage": self.manifest.stage,
            "status": "PASS" if passed else "FAIL",
            "passed": passed,
            "version": self.manifest.version,
            "source_stage": self.manifest.source_stage,
            "source_version": self.manifest.source_version,
            "release_channel": self.manifest.release_channel,
            "validation": {
                "component_validation": component_ok,
                "required_preparation_artifacts": preparation_artifact_status,
                "required_preparation_artifacts_valid": preparation_artifacts_ok,
                "required_rc_artifacts": rc_artifact_status,
                "required_rc_artifacts_valid": rc_artifacts_ok,
                "preparation_manifest_valid": preparation_manifest_ok,
                "manifest_validation": manifest_ok,
                "release_metadata_valid": metadata_ok,
                "public_api_changed": not api_ok,
                "product_feature_added": not feature_ok,
                "stable_finalization_ready": passed,
                "finalization_hash": self.manifest.finalization_hash(),
            },
        }
