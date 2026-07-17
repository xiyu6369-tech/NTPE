from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime
import hashlib
import json
import re


UTC_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


@dataclass(frozen=True)
class SingleChunkExecutionAuthorization:
    authorization_id: str
    authorized_at: str
    expires_at: str
    document_id: str
    chunk_id: str
    source_hash: str
    production_translation_hash: str
    rollback_baseline_hash: str
    provider: str
    model: str
    source_profile: str
    target_profile: str
    max_provider_requests: int = 2
    max_network_requests: int = 2
    timeout_seconds: int = 20
    retry_limit: int = 0
    allow_draft_request: bool = True
    allow_polish_request: bool = True
    allow_semantic_verification: bool = True
    allow_output_replacement: bool = False
    allow_resume_write: bool = False
    allow_cache_write: bool = False
    allow_store_write: bool = False
    allow_cross_provider_fallback: bool = False
    allow_automatic_rollout: bool = False
    explicit_execution_authorization: bool = False
    reviewer_identity_hash: str = ""
    authorization_fingerprint: str = ""


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def authorization_fingerprint(value: SingleChunkExecutionAuthorization) -> str:
    payload = asdict(value)
    payload.pop("authorization_fingerprint", None)
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def seal_authorization(**values: object) -> SingleChunkExecutionAuthorization:
    item = SingleChunkExecutionAuthorization(**values)
    return replace(item, authorization_fingerprint=authorization_fingerprint(item))


def _timestamp(value: str) -> datetime:
    if not isinstance(value, str) or not UTC_TIMESTAMP.fullmatch(value):
        raise ValueError("malformed_timestamp")
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")


def validate_execution_authorization(
    value: SingleChunkExecutionAuthorization | None,
    *,
    now: str,
    document_id: str,
    chunk_id: str,
    source_hash: str,
    production_translation_hash: str,
    rollback_baseline_hash: str,
    provider: str,
    model: str,
    source_profile: str,
    target_profile: str,
) -> tuple[bool, tuple[str, ...]]:
    if value is None:
        return False, ("missing_authorization",)
    reasons: list[str] = []
    try:
        authorized_at, expires_at, current = (_timestamp(x) for x in (value.authorized_at, value.expires_at, now))
        if authorized_at > current:
            reasons.append("authorized_at_in_future")
        if authorized_at >= expires_at:
            reasons.append("invalid_authorization_interval")
        if expires_at <= current:
            reasons.append("authorization_expired")
    except ValueError:
        reasons.append("malformed_timestamp")
    if not value.explicit_execution_authorization:
        reasons.append("explicit_execution_authorization_missing")
    expected = (
        (value.document_id, document_id, "document"),
        (value.chunk_id, chunk_id, "chunk"),
        (value.source_hash, source_hash, "source_hash"),
        (value.production_translation_hash, production_translation_hash, "production_translation_hash"),
        (value.rollback_baseline_hash, rollback_baseline_hash, "rollback_baseline_hash"),
        (value.provider, provider, "provider"),
        (value.model, model, "model"),
        (value.source_profile, source_profile, "source_profile"),
        (value.target_profile, target_profile, "target_profile"),
    )
    reasons.extend(f"{name}_mismatch" for actual, wanted, name in expected if actual != wanted)
    if value.max_provider_requests not in (1, 2) or value.max_network_requests not in (1, 2):
        reasons.append("invalid_request_budget")
    if value.max_network_requests < value.max_provider_requests:
        reasons.append("network_budget_below_provider_budget")
    if value.timeout_seconds <= 0 or value.timeout_seconds > 25:
        reasons.append("invalid_timeout")
    if value.retry_limit != 0:
        reasons.append("retry_forbidden")
    if not value.allow_draft_request or not value.allow_semantic_verification:
        reasons.append("required_execution_step_not_authorized")
    forbidden = (
        value.allow_output_replacement,
        value.allow_resume_write,
        value.allow_cache_write,
        value.allow_store_write,
        value.allow_cross_provider_fallback,
        value.allow_automatic_rollout,
    )
    if any(forbidden):
        reasons.append("forbidden_capability_authorized")
    if not value.reviewer_identity_hash:
        reasons.append("missing_reviewer_identity")
    if value.authorization_fingerprint != authorization_fingerprint(value):
        reasons.append("authorization_fingerprint_mismatch")
    return not reasons, tuple(dict.fromkeys(reasons))
