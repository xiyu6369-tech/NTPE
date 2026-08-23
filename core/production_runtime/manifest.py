"""NTPE 1.0 Beta Stage-01 Production Runtime manifest."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

VERSION = "ntpe-1.0-beta-stage-01"


def build_production_runtime_manifest(metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "name": "ntpe_production_runtime",
        "version": VERSION,
        "stage": "NTPE 1.0 Beta Stage-01",
        "components": [
            "RuntimeHost",
            "RuntimeScheduler",
            "RuntimeSessionManager",
            "RuntimeCheckpointStore",
            "RuntimeRecoveryManager",
            "RuntimeMetrics",
            "RuntimeTelemetry",
        ],
        "capabilities": [
            "production_host",
            "job_scheduler",
            "session_lock",
            "checkpoint",
            "resume",
            "recovery",
            "metrics",
            "telemetry",
            "knowledge_runtime_bridge",
        ],
        "metadata": dict(metadata or {}),
    }


def get_canonical_artifact_root(root: str | Path) -> Path:
    """Return the canonical artifacts root directory."""
    return Path(root).resolve() / "artifacts"


def get_te_v7_stage_path(root: str | Path, stage: str) -> Path:
    """Return the canonical path for a TE-v7 stage artifact directory.

    Args:
        root: Project root directory
        stage: Stage identifier (e.g., "te_v7_stage09", "te_v7_stage109")

    Returns:
        Path to the stage artifact directory
    """
    return get_canonical_artifact_root(root) / stage


def get_te_v7_artifact_path(root: str | Path, stage: str, artifact_name: str) -> Path:
    """Return the canonical path for a specific TE-v7 artifact file.

    Args:
        root: Project root directory
        stage: Stage identifier (e.g., "te_v7_stage09")
        artifact_name: Name of the artifact file

    Returns:
        Path to the artifact file
    """
    return get_te_v7_stage_path(root, stage) / artifact_name


# TE-v7 Stage artifact name constants
TE_V7_STAGE09_BASELINE = "TE_V7_STAGE09_BASELINE.json"
TE_V7_STAGE09_CANDIDATE = "TE_V7_STAGE09_CANDIDATE.json"
TE_V7_STAGE09_COMPARISON = "TE_V7_STAGE09_COMPARISON.json"
TE_V7_STAGE09_READINESS = "TE_V7_STAGE09_READINESS.json"

TE_V7_STAGE081_PRODUCTION_ACTIVATION_POLICY = "TE_V7_STAGE081_PRODUCTION_ACTIVATION_POLICY.json"
TE_V7_STAGE082_PROFILE_AWARE_CONTEXT_BUDGET = "TE_V7_STAGE082_PROFILE_AWARE_CONTEXT_BUDGET.json"
TE_V7_STAGE083_ADAPTIVE_CONTEXT_STRATEGY_SELECTION = "TE_V7_STAGE083_ADAPTIVE_CONTEXT_STRATEGY_SELECTION.json"

TE_V7_STAGE075_CANARY_AB_QUALITY_VALIDATION = "TE_V7_STAGE075_CANARY_AB_QUALITY_VALIDATION.json"
TE_V7_STAGE06_CANARY_PRODUCTION_VALIDATION = "TE_V7_STAGE06_CANARY_PRODUCTION_VALIDATION.json"
TE_V7_STAGE04_PRODUCTION_SHADOW_VALIDATION = "TE_V7_STAGE04_PRODUCTION_SHADOW_VALIDATION.json"

TE_V7_STAGE109_REAL_PROVIDER_PREFLIGHT = "TE_V7_STAGE109_REAL_PROVIDER_PREFLIGHT.json"
TE_V7_STAGE108_FAKE_TRANSPORT_FREEZE = "TE_V7_STAGE108_FAKE_TRANSPORT_FREEZE.json"

TE_V7_STAGE1010_SINGLE_REAL_INVOCATION = "TE_V7_STAGE1010_SINGLE_REAL_INVOCATION.json"
TE_V7_STAGE10101_CONTROLLED_RETRY = "TE_V7_STAGE10101_CONTROLLED_RETRY.json"
TE_V7_STAGE10101_TRANSLATION_REVIEW = "TE_V7_STAGE10101_TRANSLATION_REVIEW.txt"


__all__ = [
    "VERSION",
    "build_production_runtime_manifest",
    "get_canonical_artifact_root",
    "get_te_v7_stage_path",
    "get_te_v7_artifact_path",
    "TE_V7_STAGE09_BASELINE",
    "TE_V7_STAGE09_CANDIDATE",
    "TE_V7_STAGE09_COMPARISON",
    "TE_V7_STAGE09_READINESS",
    "TE_V7_STAGE081_PRODUCTION_ACTIVATION_POLICY",
    "TE_V7_STAGE082_PROFILE_AWARE_CONTEXT_BUDGET",
    "TE_V7_STAGE083_ADAPTIVE_CONTEXT_STRATEGY_SELECTION",
    "TE_V7_STAGE075_CANARY_AB_QUALITY_VALIDATION",
    "TE_V7_STAGE06_CANARY_PRODUCTION_VALIDATION",
    "TE_V7_STAGE04_PRODUCTION_SHADOW_VALIDATION",
    "TE_V7_STAGE109_REAL_PROVIDER_PREFLIGHT",
    "TE_V7_STAGE108_FAKE_TRANSPORT_FREEZE",
    "TE_V7_STAGE1010_SINGLE_REAL_INVOCATION",
    "TE_V7_STAGE10101_CONTROLLED_RETRY",
    "TE_V7_STAGE10101_TRANSLATION_REVIEW",
]
