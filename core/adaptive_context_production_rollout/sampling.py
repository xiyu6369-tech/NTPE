from __future__ import annotations

import hashlib

from .model import SamplingDecision

BUCKET_COUNT = 10_000
MAX_ROLLOUT_PERCENT = 5


def deterministic_rollout_sample(
    source_hash: str,
    chunk_index: int,
    profile: str,
    rollout_policy_version: str,
    rollout_percent: int,
) -> SamplingDecision:
    percent = int(rollout_percent)
    if percent < 0 or percent > MAX_ROLLOUT_PERCENT:
        percent = 0
    material = "\x1f".join((str(source_hash), str(int(chunk_index)), str(profile).lower(), str(rollout_policy_version)))
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    bucket = int(digest[:16], 16) % BUCKET_COUNT
    return SamplingDecision(
        bucket=bucket,
        rollout_percent=percent,
        policy_version=str(rollout_policy_version),
        sampled=percent > 0 and bucket < percent * 100,
        key_sha256=digest,
    )
