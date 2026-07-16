from __future__ import annotations

import json
from dataclasses import asdict

from .models import *
from .validation import reject_unsafe_payload


def canonical_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def serialize_verification_result(result: SemanticVerificationResult) -> str:
    payload = asdict(result)
    payload["status"] = result.status.value
    payload["decision"] = result.decision.value
    reject_unsafe_payload(payload)
    return canonical_json(payload)


def deserialize_verification_result(payload: str) -> SemanticVerificationResult:
    try: value = json.loads(payload)
    except (TypeError, json.JSONDecodeError) as exc: raise ValueError("malformed JSON") from exc
    reject_unsafe_payload(value)
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION: raise ValueError("unknown schema")
    try:
        status = VerificationStatus(value["status"]); decision = VerificationDecision(value["decision"])
        issues = tuple(SemanticIssue(**x) for x in value["issues"])
        evidence = SemanticVerificationEvidence(**value["evidence"])
        return SemanticVerificationResult(status, decision, issues, tuple(value["checked_invariants"]), tuple(value["unverifiable_invariants"]), value["policy_version"], value["source_hash"], value["draft_hash"], value["polish_hash"], value["deterministic_fingerprint"], value["explanation"], evidence, value["schema_version"])
    except (KeyError, TypeError, ValueError) as exc: raise ValueError("invalid verification result") from exc


def validate_verification_result(result: SemanticVerificationResult) -> None:
    if result.status is VerificationStatus.PASSED and result.decision is not VerificationDecision.ACCEPT_POLISH: raise ValueError("passed result decision mismatch")
    if result.status is not VerificationStatus.PASSED and result.decision is VerificationDecision.ACCEPT_POLISH: raise ValueError("non-passed result cannot accept polish")
    if any(x.severity not in {"review", "blocking", "critical"} for x in result.issues): raise ValueError("invalid issue type or severity")
