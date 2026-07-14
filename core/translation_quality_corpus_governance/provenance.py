from __future__ import annotations

APPROVAL_SOURCE = "human_governance_review"
GOVERNANCE_SCHEMA_VERSION = "te-v7.1-stage11.6"
FORBIDDEN_APPROVER_IDENTITIES = {
    "provider", "runtime", "planner", "metrics", "quality_engine", "automatic",
    "system", "model", "llm", "benchmark", "comparison",
}


def validate_human_actor(actor: str) -> str:
    normalized = actor.strip().lower().replace("-", "_").replace(" ", "_")
    tokens = set(normalized.split("_"))
    if not normalized or normalized in FORBIDDEN_APPROVER_IDENTITIES or not tokens.isdisjoint(FORBIDDEN_APPROVER_IDENTITIES):
        raise ValueError("governance action requires human provenance")
    return actor

