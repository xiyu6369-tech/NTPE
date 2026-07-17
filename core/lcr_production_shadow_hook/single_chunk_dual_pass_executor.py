from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import os
from types import MappingProxyType
from typing import Callable, Mapping

import core.post_polish_semantic_verification as semantic

from .execution_review_result import ExecutionReviewResult, SingleChunkExecutionTarget
from .review_candidate_artifact import build_review_artifact, write_review_artifact
from .single_chunk_execution_authorization import SingleChunkExecutionAuthorization, validate_execution_authorization


EXECUTION_FLAG = "LCR_SINGLE_CHUNK_DUAL_PASS_EXECUTION"
PREPARATION_FLAG = "LCR_BOUNDED_DUAL_PASS_PREPARATION"
GLOBAL_FLAG = "LCR_SHADOW_ENABLED"
KILL_SWITCH = "LCR_KILL_SWITCH"


def _enabled(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return default


def resolve_execution_flags(values: Mapping[str, object] | None = None) -> Mapping[str, bool]:
    source = os.environ if values is None else values
    return MappingProxyType({
        KILL_SWITCH: _enabled(source.get(KILL_SWITCH), True),
        GLOBAL_FLAG: _enabled(source.get(GLOBAL_FLAG)),
        PREPARATION_FLAG: _enabled(source.get(PREPARATION_FLAG)),
        EXECUTION_FLAG: _enabled(source.get(EXECUTION_FLAG)),
    })


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _blocked(reasons: tuple[str, ...]) -> ExecutionReviewResult:
    return ExecutionReviewResult("blocked", "blocked", reasons, 0, 0, (), "not_run", None, None, True)


def _request_evidence(package: Mapping[str, object]) -> Mapping[str, object]:
    encoded = json.dumps(dict(package), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    text = str(package.get("source_text") or package.get("candidate_text") or "")
    return MappingProxyType({
        "payload_fingerprint": _hash(encoded),
        "field_inventory": tuple(sorted(package)),
        "character_count": len(encoded),
        "token_estimate": max(1, len(encoded) // 4),
        "redacted_excerpt": text[:16] + ("..." if len(text) > 16 else ""),
    })


def execute_single_chunk_dual_pass_review(
    *,
    authorization: SingleChunkExecutionAuthorization | None,
    target: SingleChunkExecutionTarget,
    planning: str,
    provider: Callable[[Mapping[str, object]], str],
    artifact_directory: str,
    now: str,
    provider_id: str,
    model_id: str,
    feature_flags: Mapping[str, object] | None = None,
    target_count: int = 1,
    semantic_verifier: Callable[..., object] = semantic.verify_post_polish_semantics,
) -> ExecutionReviewResult:
    flags = resolve_execution_flags(feature_flags)
    flag_reasons = []
    if flags[KILL_SWITCH]: flag_reasons.append("global_kill_switch_active")
    if not flags[GLOBAL_FLAG]: flag_reasons.append("global_shadow_disabled")
    if not flags[PREPARATION_FLAG]: flag_reasons.append("preparation_flag_disabled")
    if not flags[EXECUTION_FLAG]: flag_reasons.append("execution_flag_disabled")
    if flag_reasons:
        return _blocked(tuple(flag_reasons))
    if target_count != 1:
        return _blocked(("target_count_must_equal_one",))
    if planning not in {"dual_pass_candidate", "selective_polish_candidate"}:
        return _blocked(("planning_not_execution_eligible",))
    if not target.source_text or _hash(target.source_text) != target.source_hash:
        return _blocked(("source_hash_mismatch",))
    if not target.production_translation or _hash(target.production_translation) != target.production_translation_hash:
        return _blocked(("production_translation_hash_mismatch",))
    if not target.rollback_baseline_hash or target.rollback_baseline_hash != target.production_translation_hash:
        return _blocked(("rollback_baseline_mismatch",))
    valid, reasons = validate_execution_authorization(
        authorization, now=now, document_id=target.document_id, chunk_id=target.chunk_id,
        source_hash=target.source_hash, production_translation_hash=target.production_translation_hash,
        rollback_baseline_hash=target.rollback_baseline_hash, provider=provider_id, model=model_id,
        source_profile=target.source_profile, target_profile=target.target_profile,
    )
    if not valid:
        return _blocked(reasons)
    assert authorization is not None
    requests = 0
    evidence: list[Mapping[str, object]] = []

    def network_count() -> int:
        value = getattr(provider, "network_requests", requests)
        return value if isinstance(value, int) and value >= 0 else requests

    def call(package: Mapping[str, object]) -> str:
        nonlocal requests
        if requests >= authorization.max_provider_requests:
            raise RuntimeError("request_budget_exhausted")
        requests += 1
        evidence.append(_request_evidence(package))
        value = provider(MappingProxyType(dict(package)))
        if network_count() > authorization.max_network_requests:
            raise RuntimeError("network_request_budget_exhausted")
        if not isinstance(value, str) or not value.strip():
            raise ValueError("empty_or_malformed_provider_response")
        return value

    try:
        if planning == "selective_polish_candidate":
            draft = target.production_translation
        else:
            draft = call({"request_kind": "draft", "source_text": target.source_text, "bounded_context": dict(target.bounded_context), "glossary_subset": dict(target.glossary_subset), "source_profile": target.source_profile, "target_profile": target.target_profile})
        polish = draft
        if authorization.allow_polish_request:
            polish = call({"request_kind": "polish", "source_text": target.source_text, "candidate_text": draft, "bounded_context": dict(target.bounded_context), "glossary_subset": dict(target.glossary_subset), "target_profile": target.target_profile})
    except Exception as exc:
        return ExecutionReviewResult("failed", "provider_failed", (type(exc).__name__,), requests, network_count(), tuple(evidence), "not_run", None, None, True)
    try:
        item = semantic.create_verification_input(
            verification_id=f"batch106-{authorization.authorization_id}", document_id=target.document_id,
            chunk_index=target.chunk_index, source_language=target.source_profile, target_language=target.target_profile,
            source_text=target.source_text, verified_draft_text=draft, polish_text=polish,
            polish_scope={"scope_type": "full_chunk"}, character_memory_fingerprint=_hash("bounded-character-view"),
            context_scene_fingerprint=_hash("bounded-context-view"), glossary_fingerprint=_hash(json.dumps(dict(target.glossary_subset), sort_keys=True)),
            semantic_policy_id=semantic.POLICY_ID, semantic_policy_version=semantic.POLICY_VERSION, created_at=now,
        )
        verification = semantic_verifier(item)
    except Exception as exc:
        return ExecutionReviewResult("failed", "semantic_failed", (type(exc).__name__,), requests, network_count(), tuple(evidence), "invalid_input", None, None, True)
    status = getattr(verification.status, "value", str(verification.status))
    if status == "failed":
        return ExecutionReviewResult("completed", "semantic_failed", (), requests, network_count(), tuple(evidence), status, None, None, True)
    if status != "passed":
        return ExecutionReviewResult("completed", "insufficient_evidence", (), requests, network_count(), tuple(evidence), status, None, None, True)
    artifact = build_review_artifact({
        "schema_version": "1.0", "batch": "10.6", "authorization_fingerprint": authorization.authorization_fingerprint,
        "document_id": target.document_id, "chunk_id": target.chunk_id, "source_hash": target.source_hash,
        "production_translation_hash": target.production_translation_hash, "draft_hash": _hash(draft), "polish_hash": _hash(polish),
        "candidate_text": polish, "semantic_verification_result": status, "rollback_baseline_identity": target.rollback_baseline_hash,
        "provider": provider_id, "model": model_id, "provider_request_count": requests, "network_request_count": network_count(),
        "request_evidence": [dict(x) for x in evidence], "formal_translation_replaced": False,
    })
    try:
        path, digest = write_review_artifact(artifact_directory, artifact)
    except Exception as exc:
        return ExecutionReviewResult("failed", "artifact_failed", (type(exc).__name__,), requests, network_count(), tuple(evidence), status, None, None, True)
    return ExecutionReviewResult("completed", "verified_candidate", (), requests, network_count(), tuple(evidence), status, path, digest, False)
