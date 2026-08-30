from __future__ import annotations

from dataclasses import asdict, replace
import json

import pytest
import core.controlled_provider_routing as pr

T0="2026-07-16T00:00:00Z"


def budget(**changes):
    values=dict(maximum_requests_per_chunk=2,maximum_requests_per_document=100,maximum_retry_requests=1,maximum_fallback_requests=1,maximum_polish_requests=1,maximum_total_input_tokens=10000,maximum_total_output_tokens=5000,maximum_wall_clock_seconds=360);values.update(changes);return pr.ProviderRequestBudget(**values)


def timeout(**changes):
    values=dict(per_attempt_timeout_seconds=180,maximum_chunk_wall_clock_seconds=360,maximum_document_timeout_events=3,provider_timeout_history=(),timeout_risk_level="low");values.update(changes);return pr.ProviderTimeoutBudget(**values)


def evidence(kind="read_timeout",count=1,provider="nvidia-meta-llama-3.2-90b-vision-instruct",model="meta/llama-3.2-90b-vision-instruct"):
    return pr.ProviderFailureEvidence("e-"+kind,provider,model,kind,"prompt-v1",count,180 if "timeout" in kind else None,True,True,T0)


def routing_input(**changes):
    values=dict(document_id="doc",chunk_index=0,source_language="ko",target_language="zh-Hant",language_profile_id="literary-ko-zh-hant",language_profile_version="1.0",language_profile_fingerprint="1"*64,prompt_identity="prompt-v1",context_identity="context-v1",glossary_identity="glossary-v1",quality_policy_identity="literary-fidelity-zh-hant@1.0",semantic_policy_identity="semantic@1.0",semantic_verification_available=True,translation_mode="single_pass",draft_required=True,polish_required=False,estimated_input_tokens=1000,estimated_output_tokens=500,chunk_length=1000,provider_health_evidence={p.provider_id:"healthy" for p in pr.PROVIDER_PROFILES},provider_failure_history=(),cache_availability=False,verified_draft_available=False,request_budget=budget(),timeout_budget=timeout(),current_requests=0,current_document_requests=0,current_retry_requests=0,current_fallback_requests=0,current_polish_requests=0,current_input_tokens=0,current_output_tokens=0,current_wall_clock_seconds=0,manual_approval_granted=True,created_at=T0);values.update(changes);return pr.create_routing_input(**values)


def test_provider_profiles_are_experimental_offline_and_secret_free():
    assert {p.provider_id for p in pr.PROVIDER_PROFILES}=={"nvidia-meta-llama-3.2-90b-vision-instruct","gemini-2.5-flash"}
    for p in pr.PROVIDER_PROFILES:
        forbidden=("api"+"_key","author"+"ization","creden"+"tial","http"+"://","https"+"://","?"+"key=")
        text=repr(p).lower();assert p.status=="experimental" and not any(x in text for x in forbidden)
        pr.validate_provider_profile(p)


def test_profile_fingerprint_deterministic_and_contract_sensitive():
    p=pr.NVIDIA_PROFILE
    assert p.fingerprint==pr.build_provider_profile_fingerprint(p)
    assert p.fingerprint!=pr.build_provider_profile_fingerprint(replace(p,model_id="changed"))
    assert p.fingerprint!=pr.build_provider_profile_fingerprint(replace(p,quality_contract_version="2.0"))


@pytest.mark.parametrize("kind,retry,fallback",[("read_timeout",True,True),("resource_exhausted",True,True),("authentication_failure",False,False),("invalid_request",False,False),("quality_failure",False,False),("semantic_failure",False,False),("empty_response",True,True),("policy_failure",False,False)])
def test_failure_classification(kind,retry,fallback):
    result=pr.classify_provider_failure(kind);assert result["retryable"] is retry and result["fallback_eligible"] is fallback
    if kind in {"quality_failure","semantic_failure"}:assert not result["network_failure"]


def test_unknown_failure_type_fails_closed():
    with pytest.raises(ValueError):pr.classify_provider_failure("magic")


def test_retry_allowed_once_and_deterministic():
    item=routing_input(provider_failure_history=(evidence(),));result=pr.evaluate_retry_eligibility(item,pr.NVIDIA_PROFILE,evidence(),attempts_for_provider=0)
    assert result.retry_allowed and result==pr.evaluate_retry_eligibility(item,pr.NVIDIA_PROFILE,evidence(),attempts_for_provider=0)


@pytest.mark.parametrize("kind",["authentication_failure","invalid_request","policy_failure","semantic_failure","quality_failure"])
def test_non_retryable_failures_block(kind):
    assert not pr.evaluate_retry_eligibility(routing_input(),pr.NVIDIA_PROFILE,evidence(kind),attempts_for_provider=0).retry_allowed


def test_retry_limits_and_repeated_timeout_block():
    assert not pr.evaluate_retry_eligibility(routing_input(),pr.NVIDIA_PROFILE,evidence(),attempts_for_provider=1).retry_allowed
    repeated=evidence(count=2);item=routing_input(provider_failure_history=(repeated,))
    assert "repeated_identical_timeout" in pr.evaluate_retry_eligibility(item,pr.NVIDIA_PROFILE,repeated,attempts_for_provider=0).reasons


def test_fallback_requires_manual_approval_by_default_then_can_be_allowed():
    item=routing_input(manual_approval_granted=False,provider_failure_history=(evidence(),))
    pending=pr.evaluate_fallback_eligibility(item,pr.NVIDIA_PROFILE,pr.GEMINI_PROFILE,evidence())
    assert pending.status=="manual_approval_required" and not pending.fallback_allowed
    allowed=pr.evaluate_fallback_eligibility(replace(item,manual_approval_granted=True),pr.NVIDIA_PROFILE,pr.GEMINI_PROFILE,evidence())
    assert allowed.status=="allowed" and allowed.fallback_allowed


@pytest.mark.parametrize("kind",["authentication_failure","invalid_request","quality_failure","semantic_failure","policy_failure"])
def test_ineligible_failures_never_fallback(kind):
    result=pr.evaluate_fallback_eligibility(routing_input(),pr.NVIDIA_PROFILE,pr.GEMINI_PROFILE,evidence(kind))
    assert result.status=="blocked" and not result.fallback_allowed


def test_quality_or_language_incompatibility_blocks_fallback():
    bad_quality=replace(pr.GEMINI_PROFILE,quality_contract_id="other",fingerprint="")
    bad_quality=replace(bad_quality,fingerprint=pr.build_provider_profile_fingerprint(bad_quality))
    assert pr.evaluate_fallback_eligibility(routing_input(),pr.NVIDIA_PROFILE,bad_quality,evidence()).status=="blocked"
    item=routing_input(source_language="fr")
    with pytest.raises(ValueError):pr.evaluate_fallback_eligibility(item,pr.NVIDIA_PROFILE,pr.GEMINI_PROFILE,evidence())


def test_unknown_health_requires_manual_review():
    item=routing_input(provider_health_evidence={pr.NVIDIA_PROFILE.provider_id:"healthy",pr.GEMINI_PROFILE.provider_id:"unknown"},manual_approval_granted=False)
    result=pr.evaluate_fallback_eligibility(item,pr.NVIDIA_PROFILE,pr.GEMINI_PROFILE,evidence())
    assert result.status=="manual_approval_required"


def test_academic_degraded_fallback_is_forbidden():
    academic=replace(pr.GEMINI_PROFILE,provider_id="academic-degraded",fingerprint="");academic=replace(academic,fingerprint=pr.build_provider_profile_fingerprint(academic))
    result=pr.evaluate_fallback_eligibility(routing_input(),pr.NVIDIA_PROFILE,academic,evidence())
    assert not result.fallback_allowed and "academic_degraded_fallback_forbidden" in result.reasons


@pytest.mark.parametrize("mode,verified,planned",[("single_pass",False,1),("dual_pass",False,2),("selective_polish",True,1)])
def test_mode_request_budget_is_bounded(mode,verified,planned):
    item=routing_input(translation_mode=mode,verified_draft_available=verified,draft_required=not verified,polish_required=mode!="single_pass")
    result=pr.select_provider_route(item,pr.PROVIDER_PROFILES)
    assert result.estimated_requests==planned and result.maximum_requests==2


def test_budget_token_wall_clock_and_negative_fail_closed():
    for item in (routing_input(request_budget=budget(maximum_total_input_tokens=100)),routing_input(request_budget=budget(maximum_wall_clock_seconds=100)),routing_input(current_requests=2)):
        assert pr.select_provider_route(item,pr.PROVIDER_PROFILES).decision=="blocked"
    with pytest.raises(ValueError):pr.validate_budget(budget(maximum_retry_requests=-1))


def test_cache_and_verified_draft_take_priority():
    assert pr.select_provider_route(routing_input(cache_availability=True),pr.PROVIDER_PROFILES).decision=="use_cached_result"
    health={p.provider_id:"timeout_prone" for p in pr.PROVIDER_PROFILES}
    assert pr.select_provider_route(routing_input(verified_draft_available=True,provider_health_evidence=health),pr.PROVIDER_PROFILES).decision=="reuse_verified_draft"


def test_degraded_provider_forbids_full_dual_pass():
    health={p.provider_id:"healthy" for p in pr.PROVIDER_PROFILES};health[pr.NVIDIA_PROFILE.provider_id]="degraded"
    result=pr.select_provider_route(routing_input(translation_mode="dual_pass",provider_health_evidence=health),pr.PROVIDER_PROFILES)
    assert result.decision=="blocked" and "full_dual_pass_forbidden_for_degraded_provider" in result.reasons


def test_first_provider_unknown_or_unapproved_requires_manual_review():
    assert pr.select_provider_route(routing_input(manual_approval_granted=False),pr.PROVIDER_PROFILES).decision=="manual_review_required"
    health={p.provider_id:"unknown" for p in pr.PROVIDER_PROFILES}
    assert pr.select_provider_route(routing_input(provider_health_evidence=health),pr.PROVIDER_PROFILES).decision=="manual_review_required"


def test_provider_compatibility_requires_batch7_pair_and_batch6_semantics():
    result=pr.evaluate_provider_compatibility(routing_input(),pr.NVIDIA_PROFILE,required_quality_contract_id=pr.QUALITY_CONTRACT.contract_id,required_quality_contract_version="1.0",required_prompt_contract_id="ntpe-literary-structured",required_prompt_contract_version="1.0")
    assert result.compatible
    with pytest.raises(ValueError):pr.evaluate_provider_compatibility(routing_input(semantic_verification_available=False),pr.NVIDIA_PROFILE,required_quality_contract_id=pr.QUALITY_CONTRACT.contract_id,required_quality_contract_version="1.0",required_prompt_contract_id="ntpe-literary-structured",required_prompt_contract_version="1.0")


def test_route_identity_separates_provider_model_prompt_quality_and_policy():
    item=routing_input();one=pr.build_provider_route_identity(item,pr.NVIDIA_PROFILE,pr.DEFAULT_ROUTING_POLICY);two=pr.build_provider_route_identity(item,pr.GEMINI_PROFILE,pr.DEFAULT_ROUTING_POLICY)
    assert one["translation_cache_identity"]!=two["translation_cache_identity"]
    policy=replace(pr.DEFAULT_ROUTING_POLICY,version="1.1")
    changed=pr.build_provider_route_identity(item,pr.NVIDIA_PROFILE,policy)
    assert one["translation_cache_identity"]==changed["translation_cache_identity"] and one["routing_evidence_identity"]!=changed["routing_evidence_identity"]


def test_execution_plan_is_always_prepare_only_and_secret_free():
    item=routing_input();decision=pr.select_provider_route(item,pr.PROVIDER_PROFILES);plan=pr.build_provider_execution_plan(item,decision,pr.NVIDIA_PROFILE)
    assert plan.prepare_only and not plan.executed and plan.network_requests==0 and plan.maximum_requests==2
    text=repr(plan).lower();assert not any(x in text for x in ("api_key","authorization","raw request","source_text"))


def test_historical_evidence_never_claims_current_health():
    item=evidence();assert item.historical_evidence and item.current_health_unknown and item.timeout_seconds==180


def test_serialization_deterministic_and_fail_closed():
    state={"schema_version":"1.0","policy_version":"1.0","provider_id":pr.NVIDIA_PROFILE.provider_id,"failure_type":"read_timeout","request_count":1,"prepare_only":True,"executed":False,"network_requests":0}
    encoded=pr.serialize_provider_routing_state(state);assert pr.serialize_provider_routing_state(pr.deserialize_provider_routing_state(encoded))==encoded
    bad=({**state,"schema_version":"9"},{**state,"provider_id":"unknown"},{**state,"failure_type":"magic"},{**state,"request_count":-1},{**state,"output_path":"../escape"})
    for value in bad:
        with pytest.raises(ValueError):pr.deserialize_provider_routing_state(json.dumps(value))


def test_public_api_has_no_provider_client_http_executor_or_router_runtime():
    assert not {"execute_provider","send_http","translate","run_runtime","provider_client","build_prompt"}&set(pr.__all__)
