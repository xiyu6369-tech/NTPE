from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from core.adaptive_context_single_real_invocation import (
    SingleRealInvocationArtifact,
    verify_invocation_artifact,
)

from .config import ControlledProviderRetryConfig, DEFAULT_PRIOR_ARTIFACT_PATH


@dataclass(frozen=True)
class PriorTimeoutEvidence:
    artifact: SingleRealInvocationArtifact
    file_sha256: str
    raw_bytes: bytes


def validate_prior_timeout_evidence(
    config: ControlledProviderRetryConfig, *, root: str | Path,
) -> PriorTimeoutEvidence:
    base = Path(root).resolve()
    expected = (base / DEFAULT_PRIOR_ARTIFACT_PATH).resolve()
    candidate = Path(config.prior_artifact_path)
    if not candidate.is_absolute():
        candidate = base / candidate
    candidate = candidate.resolve()
    if candidate != expected:
        raise ValueError("controlled-retry-prior-artifact-path-invalid")
    try:
        raw = candidate.read_bytes()
        artifact = verify_invocation_artifact(candidate)
    except FileNotFoundError:
        raise ValueError("controlled-retry-prior-artifact-missing") from None
    except (OSError, TypeError, ValueError):
        raise ValueError("controlled-retry-prior-artifact-integrity-invalid") from None
    if artifact.stage != "TE-v7.0-Stage10.10B" or artifact.status != "single_real_invocation_failed":
        raise ValueError("controlled-retry-prior-artifact-status-invalid")
    if artifact.network_requests != 1 or not artifact.real_provider_execution:
        raise ValueError("controlled-retry-prior-network-evidence-invalid")
    if not artifact.timeout_detected:
        raise ValueError("controlled-retry-prior-timeout-required")
    if artifact.translation_output_generated:
        raise ValueError("controlled-retry-prior-translation-output-unexpected")
    return PriorTimeoutEvidence(
        artifact=artifact,
        file_sha256=hashlib.sha256(raw).hexdigest(),
        raw_bytes=raw,
    )


def assert_prior_evidence_unchanged(
    evidence: PriorTimeoutEvidence, config: ControlledProviderRetryConfig, *, root: str | Path,
) -> None:
    path = Path(root).resolve() / config.prior_artifact_path
    if path.read_bytes() != evidence.raw_bytes:
        raise RuntimeError("controlled-retry-prior-artifact-modified")
