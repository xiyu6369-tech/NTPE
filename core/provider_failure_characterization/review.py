from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping

from .classifier import classify_failure
from .decision import execution_decision
from .schema import DecisionInput, ExecutionRecord, ExecutionSummary


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _fingerprint(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def summarize_execution(execution: ExecutionRecord) -> ExecutionSummary:
    if not isinstance(execution, Mapping):
        raise TypeError("execution_record_must_be_mapping")
    classification = classify_failure(execution)
    candidate_available = bool(execution.get("review_artifact_path"))
    semantic_outcome = str(execution.get("semantic_verification_outcome") or "")
    semantic_run = semantic_outcome not in {"", "not_run", "not_run_provider_failed"}
    provider_requests = execution.get("provider_requests", 0)
    network_requests = execution.get("network_requests", 0)
    if not isinstance(provider_requests, int) or provider_requests < 0:
        raise ValueError("invalid_provider_request_count")
    if not isinstance(network_requests, int) or network_requests < 0:
        raise ValueError("invalid_network_request_count")
    production_modified = any(bool(execution.get(field)) for field in (
        "formal_output_changed", "resume_changed", "cache_changed",
        "character_store_changed", "context_store_changed",
    ))
    decision = execution_decision(DecisionInput(
        failure_type=classification.failure_type,
        authorization_consumed=bool(execution.get("authorization_consumed")),
        execution_claim_consumed=bool(execution.get("execution_claim_path")),
        provider_request_count=provider_requests,
        candidate_available=candidate_available,
        semantic_verification_run=semantic_run,
        production_modified=production_modified,
    ))
    return ExecutionSummary(
        execution_id=str(execution.get("execution_id") or ""),
        provider=str(execution.get("provider") or ""),
        model=str(execution.get("model") or ""),
        failure_type=classification.failure_type,
        classification=classification.classification,
        decision=decision.status,
        authorization_consumed=decision.authorization_consumed,
        execution_consumed=decision.execution_consumed,
        candidate_available=candidate_available,
        semantic_verification_run=semantic_run,
        rollback_required=decision.rollback_required,
        manual_review_required=decision.manual_review_required,
        production_safe=decision.production_safe,
        retry_allowed=decision.retry_allowed,
        fallback_allowed=decision.fallback_allowed,
        provider_request_count=provider_requests,
        network_request_count=network_requests,
        evidence_fingerprint=_fingerprint(dict(execution)),
    )

