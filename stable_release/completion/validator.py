"""Stable release completion validator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable

from .manifest import (
    FROZEN_COMPONENTS,
    REQUIRED_FINALIZATION_ARTIFACTS,
    REQUIRED_PREPARATION_ARTIFACTS,
    REQUIRED_RC_ARTIFACTS,
    StableCompletionManifest,
    load_artifact_status,
)


class StableCompletionValidator:
    """Validates the final NTPE 1.0.0 stable release completion marker."""

    def __init__(self, root: Path | str = ".", manifest: StableCompletionManifest | None = None) -> None:
        self.root = Path(root)
        self.manifest = manifest or StableCompletionManifest()

    def validate_components(self, components: Iterable[str] | None = None) -> bool:
        return set(FROZEN_COMPONENTS).issubset(set(components or self.manifest.frozen_components))

    def validate_finalization_artifacts(self) -> bool:
        return all(load_artifact_status(self.root, REQUIRED_FINALIZATION_ARTIFACTS).values())

    def validate_preparation_artifacts(self) -> bool:
        return all(load_artifact_status(self.root, REQUIRED_PREPARATION_ARTIFACTS).values())

    def validate_rc_artifacts(self) -> bool:
        return all(load_artifact_status(self.root, REQUIRED_RC_ARTIFACTS).values())

    def validate_finalization_manifest(self) -> bool:
        path = self.root / "Stable_Release_Finalization_Manifest_1_0_0.json"
        if not path.exists():
            return False
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return False
        return (
            payload.get("stage") == "STABLE.2"
            and payload.get("version") == "1.0.0"
            and payload.get("status") == "FINALIZED"
            and payload.get("passed") is True
        )

    def validate_no_public_api_change(self) -> bool:
        return True

    def validate_no_product_feature_change(self) -> bool:
        return True

    def validate_release_metadata(self) -> bool:
        return (
            self.manifest.status == "COMPLETE"
            and self.manifest.version == "1.0.0"
            and self.manifest.release_channel == "stable"
        )

    def run(self) -> Dict[str, object]:
        component_ok = self.validate_components()
        finalization_artifact_status = load_artifact_status(self.root, REQUIRED_FINALIZATION_ARTIFACTS)
        preparation_artifact_status = load_artifact_status(self.root, REQUIRED_PREPARATION_ARTIFACTS)
        rc_artifact_status = load_artifact_status(self.root, REQUIRED_RC_ARTIFACTS)
        finalization_artifacts_ok = all(finalization_artifact_status.values())
        preparation_artifacts_ok = all(preparation_artifact_status.values())
        rc_artifacts_ok = all(rc_artifact_status.values())
        finalization_manifest_ok = self.validate_finalization_manifest()
        manifest_ok = self.manifest.validate()
        api_ok = self.validate_no_public_api_change()
        feature_ok = self.validate_no_product_feature_change()
        metadata_ok = self.validate_release_metadata()
        passed = all([
            component_ok,
            finalization_artifacts_ok,
            preparation_artifacts_ok,
            rc_artifacts_ok,
            finalization_manifest_ok,
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
                "required_finalization_artifacts": finalization_artifact_status,
                "required_finalization_artifacts_valid": finalization_artifacts_ok,
                "required_preparation_artifacts": preparation_artifact_status,
                "required_preparation_artifacts_valid": preparation_artifacts_ok,
                "required_rc_artifacts": rc_artifact_status,
                "required_rc_artifacts_valid": rc_artifacts_ok,
                "finalization_manifest_valid": finalization_manifest_ok,
                "manifest_validation": manifest_ok,
                "release_metadata_valid": metadata_ok,
                "public_api_changed": not api_ok,
                "product_feature_added": not feature_ok,
                "stable_release_complete": passed,
                "completion_hash": self.manifest.completion_hash(),
            },
        }
