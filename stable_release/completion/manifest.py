"""NTPE 1.0 Stable Release Completion manifest.

This module is additive only. It records completion of the NTPE 1.0.0 stable
release after finalization without changing frozen product behavior or public
contracts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Dict, Iterable, Mapping

COMPLETION_STAGE = "STABLE.3"
STABLE_VERSION = "1.0.0"
SOURCE_STAGE = "STABLE.2"
SOURCE_VERSION = "1.0.0"
RELEASE_STATUS = "COMPLETE"
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
    "stable_finalization",
)

REQUIRED_FINALIZATION_ARTIFACTS: tuple[str, ...] = (
    "Stable_Release_Finalization_Manifest_1_0_0.json",
    "Stable_Release_Finalization_Hash_1_0_0.json",
    "Stable_Release_Finalization_Report_1_0_0.md",
    "README_NTPE_1_0_Stable_Final.txt",
    "README_NTPE_1_0_Stable_Release_Finalization.txt",
    "RELEASE_NOTES_NTPE_1_0_0.md",
    "CHANGELOG_STABLE_FINAL_1_0_0.md",
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

COMPLETION_OUTPUTS: tuple[str, ...] = (
    "Stable_Release_Complete_Manifest_1_0_0.json",
    "Stable_Release_Complete_Hash_1_0_0.json",
    "Stable_Release_Complete_Report_1_0_0.md",
    "README_NTPE_1_0_Stable_Release_Complete.txt",
    "CHANGELOG_STABLE_COMPLETE_1_0_0.md",
)


@dataclass(frozen=True)
class StableCompletionManifest:
    """Immutable manifest for NTPE 1.0.0 stable release completion."""

    stage: str = COMPLETION_STAGE
    status: str = RELEASE_STATUS
    version: str = STABLE_VERSION
    source_stage: str = SOURCE_STAGE
    source_version: str = SOURCE_VERSION
    release_channel: str = RELEASE_CHANNEL
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    frozen_components: tuple[str, ...] = FROZEN_COMPONENTS
    required_finalization_artifacts: tuple[str, ...] = REQUIRED_FINALIZATION_ARTIFACTS
    required_preparation_artifacts: tuple[str, ...] = REQUIRED_PREPARATION_ARTIFACTS
    required_rc_artifacts: tuple[str, ...] = REQUIRED_RC_ARTIFACTS
    completion_outputs: tuple[str, ...] = COMPLETION_OUTPUTS
    metadata: Mapping[str, str] = field(default_factory=dict)

    def validate(self) -> bool:
        return (
            self.stage == COMPLETION_STAGE
            and self.status == RELEASE_STATUS
            and self.version == STABLE_VERSION
            and self.source_stage == SOURCE_STAGE
            and self.source_version == SOURCE_VERSION
            and self.release_channel == RELEASE_CHANNEL
            and set(FROZEN_COMPONENTS).issubset(set(self.frozen_components))
            and set(REQUIRED_FINALIZATION_ARTIFACTS).issubset(set(self.required_finalization_artifacts))
            and set(REQUIRED_PREPARATION_ARTIFACTS).issubset(set(self.required_preparation_artifacts))
            and set(REQUIRED_RC_ARTIFACTS).issubset(set(self.required_rc_artifacts))
            and set(COMPLETION_OUTPUTS).issubset(set(self.completion_outputs))
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
            "required_finalization_artifacts": list(self.required_finalization_artifacts),
            "required_preparation_artifacts": list(self.required_preparation_artifacts),
            "required_rc_artifacts": list(self.required_rc_artifacts),
            "completion_outputs": list(self.completion_outputs),
            "metadata": dict(self.metadata),
        }

    def completion_hash(self) -> str:
        payload = "|".join([
            self.stage,
            self.status,
            self.version,
            self.source_stage,
            self.source_version,
            self.release_channel,
            ",".join(self.frozen_components),
            ",".join(self.required_finalization_artifacts),
            ",".join(self.required_preparation_artifacts),
            ",".join(self.required_rc_artifacts),
            ",".join(self.completion_outputs),
        ])
        return sha256(payload.encode("utf-8")).hexdigest()


def create_stable_completion_manifest(**metadata: str) -> StableCompletionManifest:
    return StableCompletionManifest(metadata=metadata)


def load_artifact_status(root: Path, required: Iterable[str]) -> Dict[str, bool]:
    return {name: (root / name).exists() for name in required}
