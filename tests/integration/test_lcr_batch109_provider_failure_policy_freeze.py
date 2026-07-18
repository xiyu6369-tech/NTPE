from dataclasses import FrozenInstanceError
import hashlib
import inspect
import json
from pathlib import Path

import pytest

from core.provider_failure_characterization import (
    DecisionInput,
    ExecutionDecision,
    ExecutionSummary,
    FailureExecutionPolicy,
    FailureType,
    classify_failure,
    execution_decision,
    execution_policy,
    get_provider_failure_policy_freeze_metadata,
    summarize_execution,
    validate_provider_failure_policy_freeze,
)
from core.shared.evidence import canonical_json_bytes


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "manifests/lcr_batch109_provider_failure_policy_freeze_manifest.json"
BATCH107 = ROOT / "audits/legacy_capability_recovery/batch10_7/LCR_BATCH107_EXECUTION_RESULT.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_failure_taxonomy_is_frozen_at_exactly_19_types():
    assert tuple(item.value for item in FailureType) == (
        "timeout", "connection_error", "dns_failure", "tls_failure",
        "authentication_failure", "authorization_failure", "quota_exceeded",
        "rate_limited", "provider_503", "provider_5xx", "provider_4xx",
        "invalid_request", "invalid_response", "truncated_response",
        "policy_refusal", "semantic_failure", "manual_block", "internal_error", "unknown",
    )


def test_public_api_names_and_signatures_are_unchanged():
    assert tuple(inspect.signature(classify_failure).parameters) == ("evidence",)
    assert tuple(inspect.signature(execution_decision).parameters) == ("value",)
    assert tuple(inspect.signature(summarize_execution).parameters) == ("execution",)
    assert get_provider_failure_policy_freeze_metadata().public_api == (
        "classify_failure", "execution_decision", "summarize_execution",
    )


@pytest.mark.parametrize(("evidence", "expected"), [
    ({"response_status_classification": "timeout"}, "timeout"),
    ({"http_status": 429}, "rate_limited"),
    ({"http_status": 503}, "provider_503"),
    ({"http_status": 401}, "authentication_failure"),
    ({"semantic_verification_outcome": "semantic_failed"}, "semantic_failure"),
    ({"message": "unmatched condition"}, "unknown"),
])
def test_frozen_classifications_remain_deterministic(evidence, expected):
    assert classify_failure(evidence) == classify_failure(dict(evidence))
    assert classify_failure(evidence).failure_type.value == expected


def test_decision_engine_is_deterministic_and_fail_closed():
    item = DecisionInput(FailureType.TIMEOUT, True, True, 1)
    assert execution_decision(item) == execution_decision(item)
    assert execution_decision(item).actions == (
        "execution_complete", "manual_review_required", "execution_consumed",
        "retry_forbidden", "fallback_forbidden", "provider_investigation_required",
    )


def test_retry_and_fallback_are_forbidden_for_every_failure_type():
    assert all(not execution_policy(item).retry_allowed for item in FailureType)
    assert all(not execution_policy(item).fallback_allowed for item in FailureType)


def test_immutable_execution_policy_decision_and_summary_contracts():
    policy = execution_policy(FailureType.TIMEOUT)
    decision = execution_decision(DecisionInput(FailureType.TIMEOUT, True, True, 1))
    summary = summarize_execution(json.loads(BATCH107.read_text(encoding="utf-8")))
    assert isinstance(policy, FailureExecutionPolicy)
    assert isinstance(decision, ExecutionDecision)
    assert isinstance(summary, ExecutionSummary)
    for item, field in ((policy, "retry_allowed"), (decision, "fallback_allowed"), (summary, "production_safe")):
        with pytest.raises(FrozenInstanceError):
            setattr(item, field, True)


def test_batch107_timeout_fixture_classification_is_unchanged():
    summary = summarize_execution(json.loads(BATCH107.read_text(encoding="utf-8")))
    assert summary.failure_type is FailureType.TIMEOUT
    assert summary.classification == "timeout"
    assert summary.decision == "manual_review_required"
    assert summary.retry_allowed is False and summary.fallback_allowed is False
    assert summary.production_safe is True


def test_freeze_metadata_and_frozen_source_hashes_match():
    metadata = get_provider_failure_policy_freeze_metadata()
    assert metadata.freeze_version == "LCR-Batch-10.9"
    assert metadata.failure_type_count == 19
    assert metadata.retry_policy == metadata.fallback_policy == "forbidden"
    assert metadata.deterministic and metadata.read_only
    assert metadata.production_integration_authorized is False
    assert validate_provider_failure_policy_freeze(ROOT) == ()
    for relative, expected in metadata.source_hashes.items():
        assert _sha(ROOT / relative) == expected


def test_manifest_is_canonical_and_all_declared_hashes_are_valid():
    payload = _manifest()
    assert MANIFEST.read_bytes() == canonical_json_bytes(payload)
    for relative, expected in payload["sha256"].items():
        assert _sha(ROOT / relative) == expected, relative


def test_batch108_fixture_hashes_are_anchored_and_unchanged():
    manifest = _manifest()
    assert len(manifest["batch108_evidence_files"]) == 8
    for relative in manifest["batch108_evidence_files"]:
        assert manifest["sha256"][relative] == _sha(ROOT / relative)


def test_freeze_boundary_adds_no_execution_or_production_authorization():
    manifest = _manifest()
    assert manifest["provider_requests"] == manifest["network_requests"] == 0
    assert manifest["production_hook_count"] == 1
    assert manifest["active_production_authorized"] is False
    assert manifest["automatic_rollout_authorized"] is False
    assert manifest["production_integration_authorized"] is False
    assert manifest["activation_gate"] == "provider_failure_policy_frozen"


def test_review_api_is_read_only_for_batch107_fixture():
    before = BATCH107.read_bytes()
    summarize_execution(json.loads(before.decode("utf-8")))
    assert BATCH107.read_bytes() == before


def test_production_hook_count_remains_one():
    calls = []
    for path in (ROOT / "core").rglob("*.py"):
        if "run_read_only_lcr_shadow_hook(package)" in path.read_text(encoding="utf-8"):
            calls.append(path.relative_to(ROOT).as_posix())
    assert calls == ["core/adaptive_context_runtime_shadow/hook.py"]

