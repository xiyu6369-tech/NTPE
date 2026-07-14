from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from pathlib import Path

from .decision_model import HumanReviewDecision

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_review_decision_integrity(
    decision: HumanReviewDecision,
    referenced_artifacts: Mapping[str, str | Path],
) -> bool:
    expected = {
        "review_artifact_sha256": decision.review_artifact_sha256,
        "metrics_sha256": decision.metrics_sha256,
        "defects_sha256": decision.defects_sha256,
    }
    if set(referenced_artifacts) != set(expected):
        raise ValueError("all and only review integrity references are required")
    for field, path in referenced_artifacts.items():
        if file_sha256(path) != expected[field]:
            raise ValueError(f"review decision integrity mismatch: {field}")
    return True

