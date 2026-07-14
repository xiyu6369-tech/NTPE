from __future__ import annotations

SCHEMA_VERSION = "te-v7.1-stage11.5"
DECISION_SOURCE = "human_review"
REQUIRED_FIELDS = (
    "decision_id",
    "review_id",
    "decision",
    "decision_source",
    "reviewer",
    "schema_version",
    "created_at",
    "decision_reason",
    "review_artifact_sha256",
    "metrics_sha256",
    "defects_sha256",
)

REVIEWER_FIELDS = ("reviewer_id", "display_name")

