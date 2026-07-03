"""NTPE 1.0 Stable Release Finalization manifest.

This module is intentionally additive. It finalizes the already prepared 1.0.0
stable release without mutating frozen product layers or public contracts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Dict, Iterable, Mapping

FINALIZATION_STAGE = "STABLE.2"
STABLE_VERSION = "1.0.0"
SOURCE_STAGE = "STABLE.1"
SOURCE_VERSION = "1.0.0"
RELEASE_STATUS = "FINALIZED"
RELEASE_CHANNEL = "stable"

FROZEN_COMPONENTS: tuple[str, ...] = (
    "foundation",
    "cli",
    "sdk",
    "integration",
    "workflow",
    "platform_services",
    "runtime_api",
    "external_api",
    "web_ui",
    "packaging",
    "release_candidate",
    "stable_preparation",
)

REQUIRED_PREPARATION_ARTIFACTS: tuple[str, ...] = (
    "Stable_Release_Preparation_Manifest_1_0_0.json",
    "Stable_Release_Preparation_Hash_1_0_0.json",
    "Stable_Release_Preparation_Report_1_0_0.md",
    "README_NTPE_1_0_Stable_Release_Preparation.txt",
    "CHANGELOG_STABLE_1_0_0.md",
)

REQUIRED_RC_ARTIFACTS: tuple[str, ...] = (
    "RC_Freeze_Manifest_RC_06.json",
    "RC_Freeze_Report_RC_06.md",
    "Regression_Report_RC_06.md",
    "Compatibility_Report_RC_06.md",
    "Translation_Regression_Report_RC_06.md",
    "Performance_Report_RC_06.md",
)

FINALIZATION_OUTPUTS: tuple[str, ...] = (
    "Stable_Release_Finalization_Manifest_1_0_0.json",
    "Stable_Release_Finalization_Hash_1_0_0.json",
    "Stable_Release_Finalization_Report_1_0_0.md",
    "README_NTPE_1_0_Stable_Final.txt",
    "RELEASE_NOTES_NTPE_1_0_0.md",
    "CHANGELOG_STABLE_FINAL_1_0_0.md",
)


@dataclass(frozen=True)
class StableFinalizationManifest:
    """Immutable manifest for finalizing NTPE 1.0.0 stable release."""

    stage: str = FINALIZATION_STAGE
    status: str = RELEASE_STATUS
    version: str = STABLE_VERSION
    source_stage: str = SOURCE_STAGE
    source_version: str = SOURCE_VERSION
    release_channel: str = RELEASE_CHANNEL
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    frozen_components: tuple[str, ...] = FROZEN_COMPONENTS
    required_preparation_artifacts: tuple[str, ...] = REQUIRED_PREPARATION_ARTIFACTS
    required_rc_artifacts: tuple[str, ...] = REQUIRED_RC_ARTIFACTS
    finalization_outputs: tuple[str, ...] = FINALIZATION_OUTPUTS
    metadata: Mapping[str, str] = field(default_factory=dict)

    def validate(self) -> bool:
        return (
            self.stage == FINALIZATION_STAGE
            and self.status == RELEASE_STATUS
            and self.version == STABLE_VERSION
            and self.source_stage == SOURCE_STAGE
            and self.source_version == SOURCE_VERSION
            and self.release_channel == RELEASE_CHANNEL
            and set(FROZEN_COMPONENTS).issubset(set(self.frozen_components))
            and set(REQUIRED_PREPARATION_ARTIFACTS).issubset(set(self.required_preparation_artifacts))
            and set(REQUIRED_RC_ARTIFACTS).issubset(set(self.required_rc_artifacts))
            and set(FINALIZATION_OUTPUTS).issubset(set(self.finalization_outputs))
        )

    def to_dict(self) -> Dict[str, object]:
        return {
            "stage": self.stage,
            "status": self.status,
            "version": self.version,
            "source_stage": self.source_stage,
            "source_version": self.source_version,
            "release_channel": self.release_channel,
            "generated_at": self.generated_at,
            "frozen_components": list(self.frozen_components),
            "required_preparation_artifacts": list(self.required_preparation_artifacts),
            "required_rc_artifacts": list(self.required_rc_artifacts),
            "finalization_outputs": list(self.finalization_outputs),
            "metadata": dict(self.metadata),
        }

    def finalization_hash(self) -> str:
        payload = "|".join([
            self.stage,
            self.status,
            self.version,
            self.source_stage,
            self.source_version,
            self.release_channel,
            ",".join(self.frozen_components),
            ",".join(self.required_preparation_artifacts),
            ",".join(self.required_rc_artifacts),
            ",".join(self.finalization_outputs),
        ])
        return sha256(payload.encode("utf-8")).hexdigest()


def create_stable_finalization_manifest(**metadata: str) -> StableFinalizationManifest:
    return StableFinalizationManifest(metadata=metadata)


def load_artifact_status(root: Path, required: Iterable[str]) -> Dict[str, bool]:
    return {name: (root / name).exists() for name in required}
