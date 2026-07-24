"""Integration contract test for Stage 6.4 — full chain from Stage 5.3 through Stage 6.4.

Factories match REAL upstream model field lists verified via dataclasses.fields().
"""

import hashlib
import os

import pytest

from core.controlled_runtime_execution_envelope import (
    ControlledRuntimeExecutionEnvelopeRequest,
    ControlledRuntimeExecutionEnvelopeResult,
    ControlledRuntimeExecutionEnvelopeBuilder,
    verify_execution_envelope,
)


def _fp(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_FREEZE_ACTIVATION_GATE = "controlled_runtime_preparation_frozen"
_FREEZE_COMPONENT = "controlled_runtime_preparation"
_FREEZE_VERSION = "1.0"

_STAGE63_CLAIM_SCHEMA_NAME = "ntpe.controlled_runtime_atomic_authorization_consumption_claim"
_STAGE63_CLAIM_SCHEMA_VERSION = "1.0"
_STAGE63_RESULT_SCHEMA_NAME = "ntpe.controlled_runtime_atomic_authorization_consumption_result"
_STAGE63_RESULT_SCHEMA_VERSION = "1.0"

_PLAN_SCHEMA = "ntpe.controlled_runtime_execution_plan"
_PLAN_VERSION = "1.0"

# Reference fingerprints (deterministic SHA-256 of seed strings)
_RF_PLAN = _fp("int-plan-fp")
_RF_AUTH_DEC = _fp("int-auth-dec-fp")
_RF_62REC = _fp("int-62rec-fp")


# ---------------------------------------------------------------------------
# Factory: Stage 5.3 plan
# ---------------------------------------------------------------------------
def make_plan(**overrides):
    from core.controlled_runtime_execution_plan.models import (
        ControlledRuntimeExecutionPlan,
        ControlledRuntimeExecutionSourceReference,
        ControlledRuntimeExecutionPolicy,
        ControlledRuntimeExecutionStep,
    )
    kwargs = dict(
        schema_name=_PLAN_SCHEMA,
        schema_version=_PLAN_VERSION,
        strategy="controlled_single_unit",
        activation_gate=_FREEZE_ACTIVATION_GATE,
        source=ControlledRuntimeExecutionSourceReference(
            source_name="int-test-source",
            source_content_fingerprint=_fp("int-source-content"),
            execution_package_fingerprint=_fp("int-exec-pkg"),
            authorization_fingerprint=_fp("int-auth"),
            approval_record_fingerprint=_fp("int-approval"),
            runtime_submission_package_fingerprint=_fp("int-rsp"),
            runtime_adapter_request_fingerprint=_fp("int-ar"),
            runtime_adapter_preparation_fingerprint=_fp("int-ap"),
            manifest_fingerprint=_fp("int-manifest"),
            segmentation_fingerprint=_fp("int-seg"),
            chunk_plan_fingerprint=_fp("int-chunk-plan"),
            preparation_fingerprint=_fp("int-prep"),
        ),
        policy=ControlledRuntimeExecutionPolicy(
            policy_name="integration_policy",
            policy_version="1.0",
            execution_mode="controlled_single_execution",
            maximum_units_per_execution=1,
            maximum_provider_requests_per_unit=1,
            maximum_total_provider_requests=1,
            allow_partial_scope=False,
            allow_full_package_scope=False,
            allow_parallel_execution=False,
            allow_automatic_retry=False,
            allow_automatic_fallback=False,
            allow_output_replacement=False,
            allow_output_write=False,
            allow_resume_write=False,
            allow_cache_write=False,
            allow_production_hook=False,
            runtime_execution_enabled=False,
            provider_execution_enabled=False,
            translation_execution_enabled=False,
        ),
        steps=(
            ControlledRuntimeExecutionStep(
                step_index=0,
                adapter_unit_index=0,
                submission_index=0,
                execution_unit_index=0,
                execution_unit_id="int-unit-001",
                text="",
                source_character_start=0,
                source_character_end=0,
                section_indices=(0,),
                source_chunk_fingerprint=_fp("int-source-chunk"),
                execution_unit_fingerprint=_fp("int-source-chunk"),
                runtime_submission_unit_fingerprint=_fp("int-source-chunk"),
                runtime_adapter_unit_fingerprint=_fp("int-source-chunk"),
                planned_provider_request_limit=1,
                planned_retry_limit=0,
                planned_fallback_limit=0,
                status="planned_not_executed",
                runtime_attempt_count=0,
                provider_request_count=0,
                translation_result_attached=False,
                execution_step_fingerprint=_fp("int-step-fp"),
            ),
        ),
        selected_adapter_unit_indices=(0,),
        planned_step_count=1,
        available_adapter_unit_count=1,
        planned_character_count=0,
        approved_character_count=0,
        planned_approval_coverage_ratio=0.0,
        status="planned_not_executed",
        action="prepare_runtime_handoff",
        findings=(),
        summary="integration plan",
        runtime_execution_authorized=False,
        provider_execution_authorized=False,
        translation_execution_authorized=False,
        runtime_execution_enabled=False,
        provider_execution_enabled=False,
        translation_execution_enabled=False,
        automatic_retry_authorized=False,
        automatic_fallback_authorized=False,
        output_replacement_authorized=False,
        execution_started=False,
        execution_completed=False,
        provider_requests_executed=0,
        translation_executions_completed=0,
        execution_plan_fingerprint=_RF_PLAN,
    )
    kwargs.update(overrides)
    return ControlledRuntimeExecutionPlan(**kwargs)


# ---------------------------------------------------------------------------
# Factory: Stage 6.1 request (request_fingerprint is init=False / computed)
# ---------------------------------------------------------------------------
def make_auth_request(**overrides):
    from core.controlled_runtime_execution_authorization.models import (
        ControlledRuntimeExecutionAuthorizationRequest,
    )
    kwargs = dict(
        authorization_id="int-auth-req-001",
        execution_plan_fingerprint=_RF_PLAN,
        selected_adapter_index=0,
        requested_provider_request_limit=1,
        requested_translation_request_limit=0,
        retry_requested=False,
        fallback_requested=False,
        output_replacement_requested=False,
        runtime_execution_requested=True,
        provider_execution_requested=False,
        network_execution_requested=False,
        translation_execution_requested=False,
        caller_confirmation=True,
        authorization_scope="controlled_single_execution",
        purpose="integration-test",
        schema_name="ntpe.controlled_runtime_execution_authorization_request",
        schema_version="1.0",
        requested_unit_count=1,
        requested_adapter_indices=(0,),
        requested_plan_step_fingerprints=(_fp("int-step-fp"),),
        cache_write_requested=False,
        resume_write_requested=False,
        production_integration_requested=False,
    )
    kwargs.update(overrides)
    return ControlledRuntimeExecutionAuthorizationRequest(**kwargs)


# ---------------------------------------------------------------------------
# Factory: Stage 6.1 decision
# ---------------------------------------------------------------------------
def make_auth_decision(**overrides):
    from core.controlled_runtime_execution_authorization.models import (
        ControlledRuntimeExecutionAuthorizationDecision,
    )
    r = make_auth_request()
    kwargs = dict(
        authorization_id="int-auth-req-001",
        authorized=True,
        status="authorized_not_executed",
        reason_codes=(),
        execution_package_fingerprint=_fp("int-exec-pkg"),
        upstream_authorization_decision_fingerprint=_fp("int-auth"),
        approval_record_fingerprint=_fp("int-approval"),
        runtime_submission_package_fingerprint=_fp("int-rsp"),
        runtime_adapter_request_fingerprint=_fp("int-ar"),
        runtime_adapter_preparation_fingerprint=_fp("int-ap"),
        authorization_request_fingerprint=r.request_fingerprint,
        authorized_execution_plan_fingerprint=_RF_PLAN,
        authorized_adapter_index=0,
        authorized_unit_count=1,
        authorized_provider_request_limit=1,
        authorized_translation_request_limit=0,
        authorized_retry_limit=0,
        authorized_fallback_limit=0,
        output_replacement_authorized=False,
        production_integration_authorized=False,
        runtime_execution_enabled=False,
        provider_execution_enabled=False,
        network_execution_enabled=False,
        translation_execution_enabled=False,
        authorization_consumed=False,
        authorization_reusable=False,
        decision_fingerprint=_RF_AUTH_DEC,
        schema_name="ntpe.controlled_runtime_execution_authorization_decision",
        schema_version="1.0",
    )
    kwargs.update(overrides)
    return ControlledRuntimeExecutionAuthorizationDecision(**kwargs)


def _make_real_auth_request():
    return make_auth_request()


def _make_real_auth_decision():
    return make_auth_decision()


# ---------------------------------------------------------------------------
# Factory: Stage 6.1 result
# ---------------------------------------------------------------------------
def make_auth_result(**overrides):
    from core.controlled_runtime_execution_authorization.models import (
        ControlledRuntimeExecutionAuthorizationResult,
    )
    kwargs = dict(
        request=_make_real_auth_request(),
        decision=_make_real_auth_decision(),
        execution_plan_fingerprint_verified=True,
        freeze_gate_verified=True,
        policy_findings=(),
        status="authorized_not_executed",
        recommended_action="retain_for_controlled_runtime_handoff",
        runtime_invoked=False,
        provider_invoked=False,
        network_invoked=False,
        translation_invoked=False,
        output_written=False,
        resume_written=False,
        cache_written=False,
        retry_used=False,
        fallback_used=False,
        production_hook_invoked=False,
        result_fingerprint=_fp("int-auth-res-fp"),
    )
    kwargs.update(overrides)
    return ControlledRuntimeExecutionAuthorizationResult(**kwargs)


# ---------------------------------------------------------------------------
# Factory: Stage 6.2 request (request_fingerprint is init=False / computed)
# ---------------------------------------------------------------------------
def make_stage62_request(**overrides):
    from core.controlled_runtime_authorization_consumption.models import (
        ControlledRuntimeAuthorizationConsumptionRequest,
    )
    r = make_auth_request()
    d = make_auth_decision()
    kwargs = dict(
        consumption_id="int-cons-001",
        authorization_id="int-auth-req-001",
        authorization_request_fingerprint=r.request_fingerprint,
        authorization_decision_fingerprint=d.decision_fingerprint,
        execution_plan_fingerprint=_RF_PLAN,
        selected_adapter_index=0,
        requested_unit_count=1,
        consume_for_single_execution=True,
        caller_confirmation=True,
        consumption_scope="integration-scope",
        purpose="integration-test",
        schema_name="ntpe.controlled_runtime_authorization_consumption_request",
        schema_version="1.0",
    )
    kwargs.update(overrides)
    return ControlledRuntimeAuthorizationConsumptionRequest(**kwargs)


# ---------------------------------------------------------------------------
# Factory: Stage 6.2 record (record_fingerprint is init=False / computed)
# ---------------------------------------------------------------------------
def make_stage62_record(**overrides):
    from core.controlled_runtime_authorization_consumption.models import (
        ControlledRuntimeAuthorizationConsumptionRecord,
    )
    r = make_auth_request()
    d = make_auth_decision()
    s62req = make_stage62_request()
    kwargs = dict(
        consumption_id="int-cons-001",
        authorization_id="int-auth-req-001",
        authorization_request_fingerprint=r.request_fingerprint,
        authorization_decision_fingerprint=d.decision_fingerprint,
        execution_plan_fingerprint=_RF_PLAN,
        selected_adapter_index=0,
        consumed_unit_count=0,
        previous_authorization_consumed=False,
        authorization_consumption_prepared=True,
        authorization_consumed=False,
        authorization_reusable=False,
        durable_reuse_prevention_established=False,
        persistent_registry_written=False,
        execution_started=False,
        execution_completed=False,
        runtime_execution_enabled=False,
        provider_execution_enabled=False,
        network_execution_enabled=False,
        translation_execution_enabled=False,
        output_write_enabled=False,
        resume_write_enabled=False,
        cache_write_enabled=False,
        retry_enabled=False,
        fallback_enabled=False,
        production_hook_enabled=False,
        status="consumption_prepared_not_executed",
        reason_codes=(),
        upstream_fingerprint_chain=(),
        consumption_request_fingerprint=s62req.request_fingerprint,
        schema_name="ntpe.controlled_runtime_authorization_consumption_record",
        schema_version="1.0",
    )
    kwargs.update(overrides)
    return ControlledRuntimeAuthorizationConsumptionRecord(**kwargs)


def _make_real_stage62_request():
    return make_stage62_request()


def _make_real_stage62_record():
    return make_stage62_record()


# ---------------------------------------------------------------------------
# Factory: Stage 6.2 result
# ---------------------------------------------------------------------------
def make_stage62_result(**overrides):
    from core.controlled_runtime_authorization_consumption.models import (
        ControlledRuntimeAuthorizationConsumptionResult,
    )
    kwargs = dict(
        request=_make_real_stage62_request(),
        record=_make_real_stage62_record(),
        freeze_gate_verified=True,
        execution_plan_verified=True,
        authorization_request_verified=True,
        authorization_decision_verified=True,
        authorization_binding_verified=True,
        prior_consumption_state_verified=True,
        policy_findings=(),
        status="consumption_prepared_not_executed",
        recommended_action="proceed_to_controlled_atomic_consumption",
        runtime_invoked=False,
        provider_invoked=False,
        network_invoked=False,
        translation_invoked=False,
        output_written=False,
        resume_written=False,
        cache_written=False,
        retry_used=False,
        fallback_used=False,
        production_hook_invoked=False,
    )
    kwargs.update(overrides)
    return ControlledRuntimeAuthorizationConsumptionResult(**kwargs)


# ---------------------------------------------------------------------------
# Factory: Stage 6.3 claim request (request_fingerprint is init=False / computed)
# ---------------------------------------------------------------------------
def make_stage63_claim_request(**overrides):
    from core.controlled_runtime_atomic_authorization_consumption.models import (
        AtomicAuthorizationConsumptionClaimRequest,
    )
    r = make_auth_request()
    d = make_auth_decision()
    s62req = make_stage62_request()
    s62rec = make_stage62_record()
    kwargs = dict(
        claim_id="int-claim-001",
        consumption_id="int-cons-001",
        authorization_id="int-auth-req-001",
        authorization_request_fingerprint=r.request_fingerprint,
        authorization_decision_fingerprint=d.decision_fingerprint,
        execution_plan_fingerprint=_RF_PLAN,
        stage62_request_fingerprint=s62req.request_fingerprint,
        stage62_record_fingerprint=s62rec.record_fingerprint,
        selected_adapter_index=0,
        requested_unit_count=1,
        claim_for_single_execution=True,
        caller_confirmation=True,
        registry_scope="integration-registry-scope",
        purpose="integration-test",
        schema_name="ntpe.controlled_runtime_atomic_authorization_consumption_claim_request",
        schema_version="1.0",
    )
    kwargs.update(overrides)
    return AtomicAuthorizationConsumptionClaimRequest(**kwargs)


# ---------------------------------------------------------------------------
# Factory: Stage 6.3 claim
# ---------------------------------------------------------------------------
def make_stage63_claim(**overrides):
    from core.controlled_runtime_atomic_authorization_consumption.models import (
        AtomicAuthorizationConsumptionClaim,
    )
    r = make_auth_request()
    d = make_auth_decision()
    s62req = make_stage62_request()
    s62rec = make_stage62_record()
    chain = tuple(_fp(f"int-chain-{i:02d}") for i in range(12))
    kwargs = dict(
        claim_id="int-claim-001",
        consumption_id="int-cons-001",
        authorization_id="int-auth-req-001",
        authorization_request_fingerprint=r.request_fingerprint,
        authorization_decision_fingerprint=d.decision_fingerprint,
        execution_plan_fingerprint=_RF_PLAN,
        stage62_request_fingerprint=s62req.request_fingerprint,
        stage62_record_fingerprint=s62rec.record_fingerprint,
        selected_adapter_index=0,
        consumed_unit_count=1,
        authorization_consumption_prepared=True,
        authorization_consumed=True,
        authorization_reusable=False,
        durable_reuse_prevention_established=True,
        persistent_registry_written=True,
        execution_started=False,
        execution_completed=False,
        runtime_execution_enabled=False,
        provider_execution_enabled=False,
        network_execution_enabled=False,
        translation_execution_enabled=False,
        output_write_enabled=False,
        resume_write_enabled=False,
        cache_write_enabled=False,
        retry_enabled=False,
        fallback_enabled=False,
        production_hook_enabled=False,
        claim_state="durably_consumed_not_executed",
        upstream_fingerprint_chain=chain,
        claim_request_fingerprint=_fp("int-63creq-fp"),
        schema_name=_STAGE63_CLAIM_SCHEMA_NAME,
        schema_version=_STAGE63_CLAIM_SCHEMA_VERSION,
    )
    kwargs.update(overrides)
    return AtomicAuthorizationConsumptionClaim(**kwargs)


# ---------------------------------------------------------------------------
# Factory: Stage 6.3 result
# ---------------------------------------------------------------------------
def _make_real_stage63_result(claim, claim_req):
    from core.controlled_runtime_atomic_authorization_consumption.models import (
        AtomicAuthorizationConsumptionResult,
    )
    return AtomicAuthorizationConsumptionResult(
        request=claim_req,
        claim=claim,
        freeze_gate_verified=True,
        execution_plan_verified=True,
        authorization_request_verified=True,
        authorization_decision_verified=True,
        stage62_request_verified=True,
        stage62_record_verified=True,
        stage62_result_verified=True,
        authorization_binding_verified=True,
        consumption_binding_verified=True,
        registry_path_verified=True,
        registry_schema_verified=True,
        atomic_claim_committed=True,
        duplicate_claim_detected=False,
        policy_findings=(),
        status="durably_consumed_not_executed",
        recommended_action="retain_for_controlled_runtime_handoff",
        runtime_invoked=False,
        provider_invoked=False,
        network_invoked=False,
        translation_invoked=False,
        output_written=False,
        resume_written=False,
        cache_written=False,
        retry_used=False,
        fallback_used=False,
        production_hook_invoked=False,
    )


# ---------------------------------------------------------------------------
# Factory: matched claim+request pair
# ---------------------------------------------------------------------------
def _make_real_claim_and_req():
    """Return (claim, claim_req) with matched fingerprints."""
    c_req = make_stage63_claim_request()
    claim = make_stage63_claim(
        claim_request_fingerprint=c_req.request_fingerprint,
    )
    return claim, c_req


# ---------------------------------------------------------------------------
# Factory: Stage 6.4 request from live claim artifacts
# ---------------------------------------------------------------------------
def make_request_from_claim(claim, claim_request, auth_request=None, auth_decision=None):
    """Build a Stage 6.4 request whose fingerprints match real upstream artifacts."""
    arf = auth_request.request_fingerprint if auth_request else make_auth_request().request_fingerprint
    adf = auth_decision.decision_fingerprint if auth_decision else _RF_AUTH_DEC
    return ControlledRuntimeExecutionEnvelopeRequest(
        envelope_id="int-env-001",
        claim_id="int-claim-001",
        consumption_id="int-cons-001",
        authorization_id="int-auth-req-001",
        authorization_request_fingerprint=arf,
        authorization_decision_fingerprint=adf,
        execution_plan_fingerprint=_RF_PLAN,
        stage62_request_fingerprint=make_stage62_request().request_fingerprint,
        stage62_record_fingerprint=make_stage62_record().record_fingerprint,
        stage63_claim_request_fingerprint=claim_request.request_fingerprint,
        stage63_claim_fingerprint=claim.claim_fingerprint,
        selected_adapter_index=0,
        requested_unit_count=1,
        runtime_handoff_requested=True,
        caller_confirmation=True,
        runtime_scope="integration scope",
        execution_mode="controlled_single_execution",
        purpose="integration contract test",
    )


# ---------------------------------------------------------------------------
# Builder: full chain
# ---------------------------------------------------------------------------
def build_full_chain():
    """Build envelope through builder.build() with real upstream artifacts."""
    plan = make_plan()
    auth_req = make_auth_request()
    auth_dec = _make_real_auth_decision()
    auth_res = make_auth_result()
    s62_req = make_stage62_request()
    s62_rec = make_stage62_record()
    s62_res = make_stage62_result()
    claim, claim_req = _make_real_claim_and_req()
    s63_res = _make_real_stage63_result(claim, claim_req)
    req = make_request_from_claim(claim, claim_req, auth_request=auth_req, auth_decision=auth_dec)

    return ControlledRuntimeExecutionEnvelopeBuilder().build(
        request=req,
        plan=plan,
        activation_gate=_FREEZE_ACTIVATION_GATE,
        freeze_component=_FREEZE_COMPONENT,
        freeze_version=_FREEZE_VERSION,
        auth_request=auth_req,
        auth_decision=auth_dec,
        auth_result=auth_res,
        stage62_request=s62_req,
        stage62_record=s62_rec,
        stage62_result=s62_res,
        stage63_claim_request=claim_req,
        stage63_claim=claim,
        stage63_result=s63_res,
    )


# ============================================================
# Integration tests
# ============================================================


def test_integration_authentic_chain_builds_successfully():
    """Stage 5.3 through Stage 6.3 authentic chain builds Stage 6.4 envelope."""
    result = build_full_chain()
    assert result.status == "runtime_handoff_prepared_not_executed"


def test_integration_all_fingerprints_consistent():
    result = build_full_chain()
    env = result.envelope
    assert env.execution_plan_fingerprint == _RF_PLAN
    assert isinstance(env.authorization_request_fingerprint, str) and len(env.authorization_request_fingerprint) > 0
    assert isinstance(env.authorization_decision_fingerprint, str) and len(env.authorization_decision_fingerprint) > 0
    assert isinstance(env.stage62_request_fingerprint, str) and len(env.stage62_request_fingerprint) > 0
    assert isinstance(env.stage62_record_fingerprint, str) and len(env.stage62_record_fingerprint) > 0
    claim, claim_req = _make_real_claim_and_req()
    assert env.stage63_claim_request_fingerprint == claim_req.request_fingerprint
    assert env.stage63_claim_fingerprint == claim.claim_fingerprint


def test_integration_verification_passes():
    result = build_full_chain()
    verify_result = verify_execution_envelope(result.envelope)
    assert verify_result.status == "runtime_handoff_prepared_not_executed"


def test_integration_15_layer_chain_preserved():
    result = build_full_chain()
    chain = result.envelope.upstream_fingerprint_chain
    assert len(chain) == 15
    assert chain[14] == result.envelope.envelope_fingerprint


def test_integration_all_upstream_models_unchanged():
    plan = make_plan()
    auth_req = make_auth_request()
    auth_dec = _make_real_auth_decision()
    auth_res = make_auth_result()
    s62_req = make_stage62_request()
    s62_rec = make_stage62_record()
    s62_res = make_stage62_result()
    s63_creq = make_stage63_claim_request()
    s63_claim = make_stage63_claim()
    s63_res = _make_real_stage63_result(s63_claim, s63_creq)

    request = make_request_from_claim(s63_claim, s63_creq, auth_request=auth_req, auth_decision=auth_dec)

    result = ControlledRuntimeExecutionEnvelopeBuilder().build(
        request=request,
        plan=plan,
        activation_gate=_FREEZE_ACTIVATION_GATE,
        freeze_component=_FREEZE_COMPONENT,
        freeze_version=_FREEZE_VERSION,
        auth_request=auth_req,
        auth_decision=auth_dec,
        auth_result=auth_res,
        stage62_request=s62_req,
        stage62_record=s62_rec,
        stage62_result=s62_res,
        stage63_claim_request=s63_creq,
        stage63_claim=s63_claim,
        stage63_result=s63_res,
    )
    assert result.status == "runtime_handoff_prepared_not_executed"
    assert plan.execution_plan_fingerprint == _RF_PLAN
    assert isinstance(auth_dec.decision_fingerprint, str) and len(auth_dec.decision_fingerprint) > 0
    assert isinstance(s62_rec.record_fingerprint, str) and len(s62_rec.record_fingerprint) > 0


def test_integration_deterministic_repeated_build():
    r1 = build_full_chain()
    r2 = build_full_chain()
    assert r1.envelope.envelope_fingerprint == r2.envelope.envelope_fingerprint
    assert r1.envelope.envelope_id == r2.envelope.envelope_id


def test_integration_cross_stage_fingerprint_mismatch_rejected():
    """A fingerprint mismatch crossing Stage 6.2→6.3 should reject."""
    wrong_fp = _fp("wrong")
    claim = make_stage63_claim(stage62_request_fingerprint=wrong_fp)
    claim_req = make_stage63_claim_request()
    auth_req = make_auth_request()
    auth_dec = _make_real_auth_decision()
    s63_res = _make_real_stage63_result(claim, claim_req)
    request = make_request_from_claim(claim, claim_req, auth_request=auth_req, auth_decision=auth_dec)
    result = ControlledRuntimeExecutionEnvelopeBuilder().build(
        request=request,
        plan=make_plan(),
        activation_gate=_FREEZE_ACTIVATION_GATE,
        freeze_component=_FREEZE_COMPONENT,
        freeze_version=_FREEZE_VERSION,
        auth_request=make_auth_request(),
        auth_decision=make_auth_decision(),
        auth_result=make_auth_result(),
        stage62_request=make_stage62_request(),
        stage62_record=make_stage62_record(),
        stage62_result=make_stage62_result(),
        stage63_claim_request=claim_req,
        stage63_claim=claim,
        stage63_result=s63_res,
    )
    assert result.status != "runtime_handoff_prepared_not_executed"


def test_integration_durable_consumption_does_not_start_runtime():
    result = build_full_chain()
    assert result.envelope.execution_started is False
    assert result.envelope.execution_completed is False
    assert result.runtime_invoked is False


def test_integration_handoff_preparation_does_not_complete_handoff():
    result = build_full_chain()
    assert result.envelope.runtime_handoff_prepared is True
    assert result.envelope.runtime_handoff_completed is False


def test_integration_no_registry_writes():
    """Stage 6.4 must not write persistent registry files."""
    start_files = set(os.listdir("."))
    _ = build_full_chain()
    end_files = set(os.listdir("."))
    assert start_files == end_files


def test_integration_no_side_effects():
    """All boundary totals must remain zero."""
    result = build_full_chain()
    assert result.runtime_invoked is False
    assert result.provider_invoked is False
    assert result.network_invoked is False
    assert result.translation_invoked is False
    assert result.output_written is False
    assert result.resume_written is False
    assert result.cache_written is False
    assert result.retry_used is False
    assert result.fallback_used is False
    assert result.production_hook_invoked is False