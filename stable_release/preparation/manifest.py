"""NTPE 1.0 Stable Release Preparation manifest.

This module is intentionally additive. It reads RC freeze intent and produces a
stable-release preparation contract without mutating frozen product layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Dict, Iterable, Mapping

STABLE_STAGE = "STABLE.1"
STABLE_VERSION = "1.0.0"
SOURCE_RC_VERSION = "1.0-rc"

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
)

REQUIRED_RC_ARTIFACTS: tuple[str, ...] = (
    "RC_Freeze_Manifest_RC_06.json",
    "RC_Freeze_Report_RC_06.md",
    "Regression_Report_RC_06.md",
    "Compatibility_Report_RC_06.md",
    "Translation_Regression_Report_RC_06.md",
    "Performance_Report_RC_06.md",
)

STABLE_OUTPUTS: tuple[str, ...] = (
    "Stable_Release_Preparation_Manifest_1_0_0.json",
    "Stable_Release_Preparation_Hash_1_0_0.json",
    "Stable_Release_Preparation_Report_1_0_0.md",
    "README_NTPE_1_0_Stable_Release_Preparation.txt",
    "CHANGELOG_STABLE_1_0_0.md",
)

@dataclass(frozen=True)
class StablePreparationManifest:
    """Immutable manifest for preparing NTPE 1.0 stable release."""

    stage: str = STABLE_STAGE
    status: str = "PREPARED"
    version: str = STABLE_VERSION
    source_version: str = SOURCE_RC_VERSION
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    frozen_components: tuple[str, ...] = FROZEN_COMPONENTS
    required_rc_artifacts: tuple[str, ...] = REQUIRED_RC_ARTIFACTS
    stable_outputs: tuple[str, ...] = STABLE_OUTPUTS
    metadata: Mapping[str, str] = field(default_factory=dict)

    def validate(self) -> bool:
        return (
            self.stage == STABLE_STAGE
            and self.status == "PREPARED"
            and self.version == STABLE_VERSION
            and self.source_version == SOURCE_RC_VERSION
            and set(FROZEN_COMPONENTS).issubset(set(self.frozen_components))
            and set(REQUIRED_RC_ARTIFACTS).issubset(set(self.required_rc_artifacts))
            and set(STABLE_OUTPUTS).issubset(set(self.stable_outputs))
        )

    def to_dict(self) -> Dict[str, object]:
        return {
            "stage": self.stage,
            "status": self.status,
            "version": self.version,
            "source_version": self.source_version,
            "generated_at": self.generated_at,
            "frozen_components": list(self.frozen_components),
            "required_rc_artifacts": list(self.required_rc_artifacts),
            "stable_outputs": list(self.stable_outputs),
            "metadata": dict(self.metadata),
        }

    def preparation_hash(self) -> str:
        payload = "|".join([
            self.stage,
            self.status,
            self.version,
            self.source_version,
            ",".join(self.frozen_components),
            ",".join(self.required_rc_artifacts),
            ",".join(self.stable_outputs),
        ])
        return sha256(payload.encode("utf-8")).hexdigest()


def create_stable_preparation_manifest(**metadata: str) -> StablePreparationManifest:
    return StablePreparationManifest(metadata=metadata)


def load_required_artifact_status(root: Path, required: Iterable[str] = REQUIRED_RC_ARTIFACTS) -> Dict[str, bool]:
    return {name: (root / name).exists() for name in required}
