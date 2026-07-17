from dataclasses import replace
import hashlib

import pytest

from core.lcr_production_shadow_hook.execution_review_result import SingleChunkExecutionTarget
from core.lcr_production_shadow_hook.single_chunk_dual_pass_executor import execute_single_chunk_dual_pass_review
from tests.unit.test_lcr_single_chunk_execution_authorization import NOW, authorization


def sha(text): return hashlib.sha256(text.encode("utf-8")).hexdigest()


ENABLED = {"LCR_KILL_SWITCH": False, "LCR_SHADOW_ENABLED": True, "LCR_BOUNDED_DUAL_PASS_PREPARATION": True, "LCR_SINGLE_CHUNK_DUAL_PASS_EXECUTION": True}


def target(**changes):
    source, production = "그는 사흘을 기다렸다.", "他等了3天。"
    values = dict(document_id="doc", chunk_id="chunk", chunk_index=0, source_text=source, source_hash=sha(source),
                  production_translation=production, production_translation_hash=sha(production), rollback_baseline_hash=sha(production),
                  source_profile="ko", target_profile="zh-Hant", bounded_context={"scene": "room"}, glossary_subset={"사흘": "三天"})
    values.update(changes)
    return SingleChunkExecutionTarget(**values)


def auth_for(item=None, **changes):
    item = item or target()
    base = dict(document_id=item.document_id, chunk_id=item.chunk_id, source_hash=item.source_hash,
                production_translation_hash=item.production_translation_hash, rollback_baseline_hash=item.rollback_baseline_hash,
                source_profile=item.source_profile, target_profile=item.target_profile)
    base.update(changes)
    return authorization(**base)


class FakeProvider:
    def __init__(self, failure=None): self.calls=[]; self.failure=failure; self.network_requests=0
    def __call__(self, package):
        self.calls.append(package)
        if self.failure and len(self.calls) == self.failure[0]: raise self.failure[1]
        return "他等了3天。" if package["request_kind"] == "draft" else "他等了三天。"


def execute(tmp_path, **changes):
    item = changes.pop("target", target())
    values = dict(authorization=auth_for(item), target=item, planning="dual_pass_candidate", provider=FakeProvider(),
                  artifact_directory=str(tmp_path / "reviews"), now=NOW, provider_id="fake-provider", model_id="fake-model",
                  feature_flags=ENABLED)
    values.update(changes)
    return execute_single_chunk_dual_pass_review(**values)


def test_verified_candidate_uses_two_requests_and_only_review_artifact(tmp_path):
    provider = FakeProvider(); result = execute(tmp_path, provider=provider)
    assert result.outcome == "verified_candidate" and result.provider_requests == 2 and result.network_requests == 0
    assert len(provider.calls) == 2 and result.artifact_path and not result.formal_translation_replaced
    assert all(not getattr(result, field) for field in ("formal_output_modified", "resume_modified", "production_cache_modified", "character_store_modified", "context_store_modified", "automatic_rollout"))


@pytest.mark.parametrize("flags", [
    {}, {**ENABLED, "LCR_KILL_SWITCH": True}, {**ENABLED, "LCR_SHADOW_ENABLED": False},
    {**ENABLED, "LCR_BOUNDED_DUAL_PASS_PREPARATION": False}, {**ENABLED, "LCR_SINGLE_CHUNK_DUAL_PASS_EXECUTION": False},
])
def test_default_off_and_each_feature_gate_block_without_calls(tmp_path, flags):
    provider = FakeProvider(); result = execute(tmp_path, provider=provider, feature_flags=flags)
    assert result.status == "blocked" and result.provider_requests == result.network_requests == 0 and not provider.calls


@pytest.mark.parametrize("changes", [{"authorization": None}, {"target_count": 0}, {"target_count": 2}, {"planning": "blocked"}])
def test_prepare_and_target_gates_block_without_calls(tmp_path, changes):
    provider = FakeProvider(); result = execute(tmp_path, provider=provider, **changes)
    assert result.status == "blocked" and not provider.calls and not (tmp_path / "reviews").exists()


@pytest.mark.parametrize("item", [
    target(source_hash="0" * 64), target(production_translation_hash="0" * 64), target(rollback_baseline_hash=""), target(rollback_baseline_hash="0" * 64),
])
def test_changed_source_translation_or_rollback_blocks(tmp_path, item):
    provider = FakeProvider(); result = execute(tmp_path, target=item, authorization=auth_for(item), provider=provider)
    assert result.status == "blocked" and not provider.calls


@pytest.mark.parametrize("failure", [(1, TimeoutError()), (1, RuntimeError("429")), (1, RuntimeError("503")), (1, ValueError("malformed")), (2, RuntimeError("polish failed"))])
def test_provider_failures_never_retry_fallback_or_write_artifact(tmp_path, failure):
    provider = FakeProvider(failure); result = execute(tmp_path, provider=provider)
    assert result.outcome == "provider_failed" and result.retry_count == 0 and not result.fallback_used
    assert len(provider.calls) == failure[0] and result.artifact_path is None


def test_empty_response_and_request_budget_exhaustion_fail_closed(tmp_path):
    empty = lambda package: ""
    assert execute(tmp_path, provider=empty).outcome == "provider_failed"
    item = target(); limited = auth_for(item, max_provider_requests=1, max_network_requests=1)
    result = execute(tmp_path, target=item, authorization=limited)
    assert result.outcome == "provider_failed" and result.provider_requests == 1


def test_actual_network_sentinel_cannot_exceed_authorized_budget(tmp_path):
    class NetworkProvider(FakeProvider):
        def __call__(self, package):
            self.network_requests += 2
            return super().__call__(package)
    provider = NetworkProvider(); result = execute(tmp_path, provider=provider)
    assert result.outcome == "provider_failed" and result.provider_requests == 2 and result.network_requests == 4


def test_selective_polish_uses_production_translation_as_explicit_input(tmp_path):
    provider = FakeProvider(); item = target(); result = execute(tmp_path, target=item, authorization=auth_for(item), planning="selective_polish_candidate", provider=provider)
    assert result.outcome == "verified_candidate" and result.provider_requests == 1
    assert provider.calls[0]["candidate_text"] == item.production_translation


def test_semantic_failure_and_insufficient_evidence_retain_production(tmp_path):
    class State: 
        def __init__(self, value): self.value=value
    class Result:
        def __init__(self, value): self.status=State(value)
    failed = execute(tmp_path, semantic_verifier=lambda item: Result("failed"))
    insufficient = execute(tmp_path, semantic_verifier=lambda item: Result("insufficient_evidence"))
    assert failed.outcome == "semantic_failed" and insufficient.outcome == "insufficient_evidence"
    assert failed.production_translation_retained and insufficient.production_translation_retained


def test_forbidden_authorization_flags_block_instead_of_downgrade(tmp_path):
    item = target()
    for field in ("allow_output_replacement", "allow_resume_write", "allow_cache_write", "allow_store_write", "allow_cross_provider_fallback", "allow_automatic_rollout"):
        provider = FakeProvider(); result = execute(tmp_path, target=item, authorization=auth_for(item, **{field: True}), provider=provider)
        assert result.status == "blocked" and not provider.calls
