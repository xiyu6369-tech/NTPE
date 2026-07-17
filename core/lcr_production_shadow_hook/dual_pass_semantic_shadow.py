from __future__ import annotations

import hashlib
import json
import time
from types import MappingProxyType
from typing import Mapping

from core.dual_pass_translation import (
    ArtifactStatus, ProviderCostEstimate, ProviderHealth, QualityStatus, SemanticStatus,
    create_draft_result, create_polish_scope, create_polish_trigger, select_translation_mode,
    build_dual_pass_execution_plan,
)
from core.post_polish_semantic_verification import create_verification_input, verify_post_polish_semantics

from .models import DualPassSemanticShadowInput, DualPassSemanticShadowResult


_ALLOWED = {
    "chunk_id", "chunk_index", "source_hash", "source_char_count", "source_language_profile_id",
    "target_language_profile_id", "translation_hash", "translation_char_count", "quality_signal_summary",
    "context_shadow_summary", "character_shadow_summary", "scene_shadow_summary",
    "provider_metadata_summary", "retry_metadata_summary", "cache_metadata_summary", "created_at",
    "synthetic_semantic_fixture",
}
_FORBIDDEN = ("api_key", "authorization", "prompt", "source_text", "translation_text", "provider_payload", "secret", "password", "path")


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


def _freeze_mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        return MappingProxyType({})
    return MappingProxyType({str(k): value[k] for k in sorted(value)})


def build_dual_pass_semantic_shadow_input(metadata: Mapping[str, object]) -> DualPassSemanticShadowInput:
    """Accept only a detached metadata summary; production text is fail-closed."""
    if not isinstance(metadata, Mapping) or set(metadata) - _ALLOWED:
        raise ValueError("unsupported shadow input fields")
    lowered = " ".join(str(key).lower() for key in metadata)
    if any(token in lowered for token in _FORBIDDEN):
        raise ValueError("forbidden production content or secret field")
    for name in ("chunk_id", "source_hash", "translation_hash", "source_language_profile_id", "target_language_profile_id"):
        if not isinstance(metadata.get(name), str) or not metadata[name]:
            raise ValueError(f"missing {name}")
    for name in ("chunk_index", "source_char_count", "translation_char_count"):
        if not isinstance(metadata.get(name), int) or isinstance(metadata[name], bool) or metadata[name] < 0:
            raise ValueError(f"invalid {name}")
    fixture = metadata.get("synthetic_semantic_fixture")
    if fixture is not None:
        if not isinstance(fixture, Mapping) or fixture.get("controlled_synthetic") is not True:
            raise ValueError("semantic fixture must be controlled synthetic")
        if any(key not in {"controlled_synthetic", "source", "draft", "polish", "scope_type"} for key in fixture):
            raise ValueError("unsupported synthetic fixture fields")
        if any(len(str(fixture.get(key, ""))) > 256 for key in ("source", "draft", "polish")):
            raise ValueError("synthetic fixture exceeds bounded limit")
        fixture = MappingProxyType({str(k): fixture[k] for k in sorted(fixture)})
    return DualPassSemanticShadowInput(
        chunk_id=str(metadata["chunk_id"]), chunk_index=int(metadata["chunk_index"]),
        source_hash=str(metadata["source_hash"]), source_char_count=int(metadata["source_char_count"]),
        source_language_profile_id=str(metadata["source_language_profile_id"]),
        target_language_profile_id=str(metadata["target_language_profile_id"]),
        translation_hash=str(metadata["translation_hash"]), translation_char_count=int(metadata["translation_char_count"]),
        quality_signal_summary=_freeze_mapping(metadata.get("quality_signal_summary")),
        context_shadow_summary=_freeze_mapping(metadata.get("context_shadow_summary")),
        character_shadow_summary=_freeze_mapping(metadata.get("character_shadow_summary")),
        scene_shadow_summary=_freeze_mapping(metadata.get("scene_shadow_summary")),
        provider_metadata_summary=_freeze_mapping(metadata.get("provider_metadata_summary")),
        retry_metadata_summary=_freeze_mapping(metadata.get("retry_metadata_summary")),
        cache_metadata_summary=_freeze_mapping(metadata.get("cache_metadata_summary")),
        synthetic_semantic_fixture=fixture, created_at=str(metadata.get("created_at", "")),
    )


def empty_dual_pass_semantic_result(status: str = "metadata_unavailable") -> DualPassSemanticShadowResult:
    return DualPassSemanticShadowResult("1.0", "10.4", status, True, False, "insufficient_evidence", "blocked", False,
        (status,), (status,), "none", False, False, True, "insufficient_evidence", (),
        MappingProxyType({"production_result_present": False, "decision_alignment": "insufficient_evidence"}))


def _signals(snapshot: DualPassSemanticShadowInput) -> tuple[bool, tuple[str, ...], tuple[str, ...]]:
    q = snapshot.quality_signal_summary
    blocked = []
    if not snapshot.translation_hash or snapshot.translation_char_count <= 0:
        blocked.append("translation_result_unavailable")
    if snapshot.provider_metadata_summary.get("provider_degraded") is True:
        blocked.append("provider_degraded")
    reasons = [key for key in ("semantic_risk", "name_consistency_risk", "pronoun_risk", "dialogue_risk", "register_risk", "repetition_risk", "short_output_risk") if q.get(key) is True]
    if snapshot.scene_shadow_summary.get("unresolved_reference_count", 0): reasons.append("unresolved_reference")
    if snapshot.retry_metadata_summary.get("retry_failed") is True: reasons.append("retry_history_risk")
    return not blocked, tuple(sorted(set(reasons))), tuple(blocked)


def evaluate_dual_pass_semantic_shadow(snapshot: DualPassSemanticShadowInput) -> DualPassSemanticShadowResult:
    """Plan through Batch 5/6 public APIs without generating or applying text."""
    started = time.perf_counter_ns()
    usable, risks, blocked = _signals(snapshot)
    if not usable:
        return _result(snapshot, "blocked", "blocked", False, (), blocked, "none", False, True, True, "would_block", ())
    if snapshot.quality_signal_summary.get("evidence_complete") is not True:
        return _result(snapshot, "insufficient_evidence", "blocked", False, ("insufficient_evidence",), (), "none", False, False, True, "insufficient_evidence", (), "insufficient_evidence")
    try:
        draft = create_draft_result(draft_id="shadow-" + snapshot.chunk_id, document_id="shadow", chunk_index=snapshot.chunk_index,
            source_hash=snapshot.source_hash, prompt_identity=_hash(snapshot.source_hash), source_language=snapshot.source_language_profile_id,
            target_language=snapshot.target_language_profile_id, draft_text="[shadow-draft]", quality_status=QualityStatus.PASSED,
            semantic_status=SemanticStatus.PASSED, created_at=snapshot.created_at or "1970-01-01T00:00:00Z", status=ArtifactStatus.VERIFIED)
        # The Batch 5 public scope contract requires explicit span boundaries
        # for selective planning.  This shadow layer has no production text,
        # so it deliberately plans the safe full-chunk shape only.
        scope_type = "full_chunk"
        scope = create_polish_scope(scope_type=scope_type, original_draft_hash=draft.draft_hash,
            selected_text="[shadow]", surrounding_context="[redacted]")
        triggers = () if not risks else (create_polish_trigger(trigger_id="shadow-risk", trigger_type="human_requested",
            evidence=({"summary": ",".join(risks)},), confidence=.9, severity="blocking", scope=scope,
            estimated_quality_value=1, estimated_cost=0),)
        decision = select_translation_mode(draft, triggers, provider_policy={"expected_source_hash": snapshot.source_hash, "health": ProviderHealth.HEALTHY.value, "rollback_available": True},
            cost_policy={"allow_second_request": True, "estimated_output_tokens": 0}, timeout_policy={"timeout_risk": 0, "maximum_dual_pass_risk": .3}, quality_policy={})
        plan = build_dual_pass_execution_plan(decision, triggers=triggers,
            cost_estimate=ProviderCostEstimate(0, 0, 0, 0, 0, 0, 0, False, 0), prepare_only=True)
    except Exception:
        return empty_dual_pass_semantic_result("invalid")
    semantic, checked = "not_applicable", ()
    if snapshot.synthetic_semantic_fixture:
        fixture = snapshot.synthetic_semantic_fixture
        item = create_verification_input(verification_id="synthetic-" + snapshot.chunk_id, document_id="synthetic",
            chunk_index=snapshot.chunk_index, source_language=snapshot.source_language_profile_id, target_language=snapshot.target_language_profile_id,
            source_text=str(fixture.get("source", "x")), verified_draft_text=str(fixture.get("draft", "x")), polish_text=str(fixture.get("polish", "x")),
            polish_scope={"scope_type": fixture.get("scope_type", "full_chunk")}, character_memory_fingerprint=str(snapshot.character_shadow_summary.get("fingerprint", _hash([]))),
            context_scene_fingerprint=str(snapshot.context_shadow_summary.get("fingerprint", _hash([]))), glossary_fingerprint=_hash([]),
            semantic_policy_id="semantic-verification-policy", semantic_policy_version="1.0", created_at=snapshot.created_at or "1970-01-01T00:00:00Z")
        verification = verify_post_polish_semantics(item)
        semantic = {"accept_polish": "would_accept_polish", "rollback_to_draft": "would_rollback_to_draft", "manual_review_required": "would_require_manual_review", "block_output": "would_block"}.get(verification.decision.value, "insufficient_evidence")
        checked = verification.checked_invariants
    mode_map = {"single_pass": "single_pass", "dual_pass": "dual_pass_full", "selective_polish": "dual_pass_selective", "blocked": "blocked"}
    mode = mode_map[decision.mode.value]
    eligibility = "single_pass_sufficient" if not risks else ("selective_polish_candidate" if mode == "dual_pass_selective" else "dual_pass_candidate")
    rollback = semantic in {"would_rollback_to_draft", "would_block"}
    manual = semantic in {"would_require_manual_review", "insufficient_evidence"}
    return _result(snapshot, "completed", mode, mode != "blocked", risks or decision.reasons, (), "dialogue" if scope_type == "dialogue_span" else ("sentence" if scope_type == "sentence_span" else "global"), plan.verification_required, rollback, manual, semantic, checked, eligibility)


def _result(snapshot: DualPassSemanticShadowInput, status: str, mode: str, eligible: bool, reasons: tuple[str, ...], blocking: tuple[str, ...], scope: str, verification: bool, rollback: bool, manual: bool, semantic: str, checked: tuple[str, ...], eligibility: str = "blocked") -> DualPassSemanticShadowResult:
    comparison = MappingProxyType({"production_result_present": bool(snapshot.translation_hash), "production_quality_gate_status": str(snapshot.quality_signal_summary.get("production_quality_gate_status", "unknown")), "shadow_dual_pass_recommended": mode in {"dual_pass_full", "dual_pass_selective"}, "shadow_semantic_verification_required": verification, "shadow_would_accept": semantic == "would_accept_polish", "shadow_would_rollback": semantic == "would_rollback_to_draft", "shadow_would_block": semantic == "would_block", "decision_alignment": "not_comparable" if semantic == "not_applicable" else "partially_aligned", "decision_divergence_reasons": list(blocking)})
    return DualPassSemanticShadowResult("1.0", "10.4", status, True, False, eligibility, mode, eligible, tuple(reasons), tuple(blocking), scope, verification, rollback, manual, semantic, tuple(checked), comparison, production_draft_generated=False, production_polish_generated=False, synthetic_planning_artifact_created=True, synthetic_planning_artifact_applied=False, duration_ms=0.0)
