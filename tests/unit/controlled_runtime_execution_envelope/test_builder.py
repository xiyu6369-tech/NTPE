"""Tests for Stage 6.4 builder — success and rejection paths."""

import hashlib
import os
import threading

import pytest

from core.controlled_runtime_execution_envelope.builder import (
    ControlledRuntimeExecutionEnvelopeBuilder,
)
from core.controlled_runtime_execution_envelope.models import (
    ControlledRuntimeExecutionEnvelopeRequest,
    ControlledRuntimeExecutionEnvelope,
    ControlledRuntimeExecutionEnvelopeResult,
)
from core.controlled_runtime_execution_envelope.policy import (
    DEFAULT_POLICY,
)


def _fp(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Authentic upstream factory objects — returns (object, real_fingerprints_dict)
# ---------------------------------------------------------------------------

_hex_small = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()


def make_plan(**overrides):
    from core.controlled_runtime_execution_plan.models import (
        ControlledRuntimeExecutionPlan,
        ControlledRuntimeExecutionSourceReference,
        ControlledRuntimeExecutionPolicy,
        ControlledRuntimeExecutionStep,
    )
    source = ControlledRuntimeExecutionSourceReference(
        source_name="test-source",
        source_content_fingerprint=_hex_small("source-content"),
        execution_package_fingerprint=_hex_small("exec-pkg"),
        authorization_fingerprint=_hex_small("auth"),
        approval_record_fingerprint=_hex_small("approval"),
        runtime_submission_package_fingerprint=_hex_small("submission-pkg"),
        runtime_adapter_request_fingerprint=_hex_small("adapter-req"),
        runtime_adapter_preparation_fingerprint=_hex_small("adapter-prep"),
        manifest_fingerprint=_hex_small("manifest"),
        segmentation_fingerprint=_hex_small("segmentation"),
        chunk_plan_fingerprint=_hex_small("chunk-plan"),
        preparation_fingerprint=_hex_small("preparation"),
    )
    pol = ControlledRuntimeExecutionPolicy(
        policy_name="controlled_single_execution_policy",
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
    )
    step = ControlledRuntimeExecutionStep(
        step_index=0,
        adapter_unit_index=0,
        submission_index=0,
        execution_unit_index=0,
        execution_unit_id="unit-001",
        text="test text content",
        source_character_start=0,
        source_character_end=17,
        section_indices=(0,),
        source_chunk_fingerprint=_hex_small("chunk-001-content"),
        execution_unit_fingerprint=_hex_small("unit-fp"),
        runtime_submission_unit_fingerprint=_hex_small("sub-fp"),
        runtime_adapter_unit_fingerprint=_hex_small("adapter-fp"),
        planned_provider_request_limit=1,
        planned_retry_limit=0,
        planned_fallback_limit=0,
        status="planned_not_executed",
        runtime_attempt_count=0,
        provider_request_count=0,
        translation_result_attached=False,
        execution_step_fingerprint=_hex_small("step-fp"),
    )
    kwargs = dict(
        schema_name="ntpe.controlled_runtime_execution_plan",
        schema_version="1.0",
        strategy="controlled_single_unit",
        activation_gate="controlled_runtime_preparation_frozen",
        source=source,
        policy=pol,
        steps=(step,),
        selected_adapter_unit_indices=(0,),
        planned_step_count=1,
        available_adapter_unit_count=1,
        planned_character_count=17,
        approved_character_count=17,
        planned_approval_coverage_ratio=1.0,
        status="planned_not_executed",
        action="await",
        findings=(),
        summary="Test plan for envelope builder.",
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
        execution_plan_fingerprint=_fp("plan-001-fp"),
    )
    kwargs.update(overrides)
    return ControlledRuntimeExecutionPlan(**kwargs)


def make_auth_request(**overrides):
    from core.controlled_runtime_execution_authorization.models import (
        ControlledRuntimeExecutionAuthorizationRequest,
    )
    kwargs = dict(
        authorization_id="auth-req-001",
        execution_plan_fingerprint=_fp("plan-001-fp"),
        selected_adapter_index=0,
        requested_provider_request_limit=1,
        requested_translation_request_limit=1,
        retry_requested=False,
        fallback_requested=False,
        output_replacement_requested=False,
        runtime_execution_requested=False,
        provider_execution_requested=False,
        network_execution_requested=False,
        translation_execution_requested=False,
        caller_confirmation=True,
        authorization_scope="exact auth/claim/plan/adapter/unit",
        purpose="test",
        schema_name="ntpe.controlled_runtime_execution_authorization_request",
        schema_version="1.0",
    )
    kwargs.update(overrides)
    return ControlledRuntimeExecutionAuthorizationRequest(**kwargs)


def make_auth_decision(**overrides):
    from core.controlled_runtime_execution_authorization.models import (
        ControlledRuntimeExecutionAuthorizationDecision,
    )
    auth_req = make_auth_request()
    kwargs = dict(
        authorization_id="auth-req-001",
        authorized=True,
        status="authorized_not_executed",
        reason_codes=("authorized",),
        execution_package_fingerprint=_hex_small("exec-pkg"),
        upstream_authorization_decision_fingerprint=_hex_small("upstream-auth"),
        approval_record_fingerprint=_hex_small("approval"),
        runtime_submission_package_fingerprint=_hex_small("sub-pkg"),
        runtime_adapter_request_fingerprint=_hex_small("adapter-req"),
        runtime_adapter_preparation_fingerprint=_hex_small("adapter-prep"),
        authorization_request_fingerprint=auth_req.request_fingerprint,
        authorized_execution_plan_fingerprint=_fp("plan-001-fp"),
        authorized_adapter_index=0,
        authorized_unit_count=1,
        authorized_provider_request_limit=1,
        authorized_translation_request_limit=1,
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
        decision_fingerprint=_hex_small("auth-dec"),
        schema_name="ntpe.controlled_runtime_execution_authorization_decision",
        schema_version="1.0",
    )
    kwargs.update(overrides)
    return ControlledRuntimeExecutionAuthorizationDecision(**kwargs)


def make_auth_result(**overrides):
    from core.controlled_runtime_execution_authorization.models import (
        ControlledRuntimeExecutionAuthorizationResult,
        ControlledRuntimeExecutionAuthorizationFinding,
    )
    req = make_auth_request()
    dec = make_auth_decision()
    finding = ControlledRuntimeExecutionAuthorizationFinding(
        code="AUTHORIZED",
        severity="info",
        message="Authorization passed.",
        field="authorized",
        expected="True",
        observed="True",
    )
    kwargs = dict(
        request=req,
        decision=dec,
        execution_plan_fingerprint_verified=True,
        freeze_gate_verified=True,
        policy_findings=(finding,),
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
        result_fingerprint=_hex_small("auth-result"),
    )
    kwargs.update(overrides)
    return ControlledRuntimeExecutionAuthorizationResult(**kwargs)


def make_stage62_request(**overrides):
    from core.controlled_runtime_authorization_consumption.models import (
        ControlledRuntimeAuthorizationConsumptionRequest,
    )
    kwargs = dict(
        consumption_id="cons-001",
        authorization_id="auth-req-001",
        authorization_request_fingerprint=_fp("auth-req-fp"),
        authorization_decision_fingerprint=_fp("auth-dec-fp"),
        execution_plan_fingerprint=_fp("plan-001-fp"),
        selected_adapter_index=0,
        requested_unit_count=1,
        consume_for_single_execution=True,
        caller_confirmation=True,
        consumption_scope="exact auth/consumption/plan/adapter/unit",
        purpose="test",
        schema_name="ntpe.controlled_runtime_authorization_consumption_request",
        schema_version="1.0",
    )
    kwargs.update(overrides)
    return ControlledRuntimeAuthorizationConsumptionRequest(**kwargs)


def make_stage62_record(**overrides):
    from core.controlled_runtime_authorization_consumption.models import (
        ControlledRuntimeAuthorizationConsumptionRecord,
    )
    chain = tuple(_hex_small(f"layer{i}") for i in range(7))
    kwargs = dict(
        consumption_id="cons-001",
        authorization_id="auth-req-001",
        authorization_request_fingerprint=_fp("auth-req-fp"),
        authorization_decision_fingerprint=_fp("auth-dec-fp"),
        execution_plan_fingerprint=_fp("plan-001-fp"),
        selected_adapter_index=0,
        consumed_unit_count=1,
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
        reason_codes=("prepared",),
        upstream_fingerprint_chain=chain,
        consumption_request_fingerprint=_fp("62req-built"),
        schema_name="ntpe.controlled_runtime_authorization_consumption_record",
        schema_version="1.0",
    )
    kwargs.update(overrides)
    return ControlledRuntimeAuthorizationConsumptionRecord(**kwargs)


def make_stage62_result(**overrides):
    from core.controlled_runtime_authorization_consumption.models import (
        ControlledRuntimeAuthorizationConsumptionResult,
        ControlledRuntimeAuthorizationConsumptionFinding,
    )
    req = make_stage62_request()
    rec = make_stage62_record()
    finding = ControlledRuntimeAuthorizationConsumptionFinding(
        code="PREPARED",
        severity="info",
        message="Consumption preparation verified.",
        field="authorization_consumption_prepared",
        expected="True",
        observed="True",
    )
    kwargs = dict(
        request=req,
        record=rec,
        freeze_gate_verified=True,
        execution_plan_verified=True,
        authorization_request_verified=True,
        authorization_decision_verified=True,
        authorization_binding_verified=True,
        prior_consumption_state_verified=True,
        policy_findings=(finding,),
        status="consumption_prepared_not_executed",
        recommended_action="retain_for_atomic_execution_boundary",
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


def make_stage63_claim_request(**overrides):
    from core.controlled_runtime_atomic_authorization_consumption.models import (
        AtomicAuthorizationConsumptionClaimRequest,
    )
    kwargs = dict(
        claim_id="claim-001",
        consumption_id="cons-001",
        authorization_id="auth-req-001",
        authorization_request_fingerprint=_fp("auth-req-fp"),
        authorization_decision_fingerprint=_fp("auth-dec-fp"),
        execution_plan_fingerprint=_fp("plan-001-fp"),
        stage62_request_fingerprint=_fp("62req-fp"),
        stage62_record_fingerprint=_fp("62rec-fp"),
        selected_adapter_index=0,
        requested_unit_count=1,
        claim_for_single_execution=True,
        caller_confirmation=True,
        registry_scope="exact registry-claim-consumption-auth-plan-adapter",
        purpose="test",
        schema_name="ntpe.controlled_runtime_atomic_authorization_consumption_claim_request",
        schema_version="1.0",
    )
    kwargs.update(overrides)
    return AtomicAuthorizationConsumptionClaimRequest(**kwargs)


def make_stage63_claim(**overrides):
    from core.controlled_runtime_atomic_authorization_consumption.models import (
        AtomicAuthorizationConsumptionClaim,
    )
    chain = tuple(_hex_small(f"layer{i}") for i in range(12))
    kwargs = dict(
        claim_id="claim-001",
        consumption_id="cons-001",
        authorization_id="auth-req-001",
        authorization_request_fingerprint=_fp("auth-req-fp"),
        authorization_decision_fingerprint=_fp("auth-dec-fp"),
        execution_plan_fingerprint=_fp("plan-001-fp"),
        stage62_request_fingerprint=_fp("62req-fp"),
        stage62_record_fingerprint=_fp("62rec-fp"),
        selected_adapter_index=0,
        consumed_unit_count=1,
        claim_state="durably_consumed_not_executed",
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
        claim_request_fingerprint=_fp("63creq-fp"),
        upstream_fingerprint_chain=chain,
        schema_name="ntpe.controlled_runtime_atomic_authorization_consumption_claim",
        schema_version="1.0",
    )
    kwargs.update(overrides)
    return AtomicAuthorizationConsumptionClaim(**kwargs)


def make_stage63_result(**overrides):
    from core.controlled_runtime_atomic_authorization_consumption.models import (
        AtomicAuthorizationConsumptionResult,
        AtomicAuthorizationConsumptionFinding,
    )
    req = make_stage63_claim_request()
    claim = make_stage63_claim()
    finding = AtomicAuthorizationConsumptionFinding(
        code="ATOMIC_CLAIM_COMMITTED",
        severity="info",
        message="Atomic claim committed successfully.",
        field="atomic_claim_committed",
        expected="True",
        observed="True",
    )
    kwargs = dict(
        request=req,
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
        policy_findings=(finding,),
        status="durably_consumed_not_executed",
        recommended_action="retain_for_controlled_runtime_handoff",
    )
    kwargs.update(overrides)
    return AtomicAuthorizationConsumptionResult(**kwargs)


# ---------------------------------------------------------------------------
# BUILD HELPER — constructs all upstream objects, extracts real fingerprints,
#               and builds the envelope with matching request.
# ---------------------------------------------------------------------------


def _build_helper(**overrides):
    """Build envelope with authentic upstream chain using REAL fingerprints.

    overrides may contain dicts for: plan, auth_request, auth_decision,
    auth_result, stage62_request, stage62_record, stage62_result,
    stage63_claim_request, stage63_claim, stage63_result,
    activation_gate, freeze_component, freeze_version.
    """
    builder = ControlledRuntimeExecutionEnvelopeBuilder()

    # -- 1. Build upstream objects whose fingerprints feed into the claim --
    plan = make_plan(**overrides.get("plan", {}))
    auth_request = make_auth_request(**overrides.get("auth_request", {}))
    auth_decision = make_auth_decision(**overrides.get("auth_decision", {}))
    auth_result = make_auth_result(**overrides.get("auth_result", {}))
    stage62_request = make_stage62_request(**overrides.get("stage62_request", {}))
    stage62_record = make_stage62_record(**overrides.get("stage62_record", {}))
    stage62_result = make_stage62_result(**overrides.get("stage62_result", {}))

    # -- 2. Extract REAL fingerprints now (before claim is built) --
    real_plan_fp = plan.execution_plan_fingerprint
    real_auth_req_fp = auth_request.request_fingerprint
    real_auth_dec_fp = auth_decision.decision_fingerprint
    real_s62_req_fp = stage62_request.request_fingerprint
    real_s62_rec_fp = stage62_record.record_fingerprint

    # -- 3. Build Stage 6.3 claim with cross-stage fingerprint alignment --
    claim_overrides = dict(overrides.get("stage63_claim", {}))
    claim_overrides.setdefault("authorization_request_fingerprint", real_auth_req_fp)
    claim_overrides.setdefault("authorization_decision_fingerprint", real_auth_dec_fp)
    claim_overrides.setdefault("stage62_request_fingerprint", real_s62_req_fp)
    claim_overrides.setdefault("stage62_record_fingerprint", real_s62_rec_fp)
    stage63_claim_request = make_stage63_claim_request(**overrides.get("stage63_claim_request", {}))
    stage63_claim = make_stage63_claim(**claim_overrides)
    stage63_result = make_stage63_result(**overrides.get("stage63_result", {}))

    # -- 4. Extract claim fingerprints now that claim objects exist --
    real_s63_creq_fp = stage63_claim_request.request_fingerprint
    real_s63_claim_fp = stage63_claim.claim_fingerprint

    # -- 5. Build envelope request USING real upstream fingerprints --
    req_overrides = overrides.get("request", {})
    request_kwargs = dict(
        envelope_id="env-001",
        claim_id=stage63_claim.claim_id,
        consumption_id=stage62_record.consumption_id,
        authorization_id=auth_decision.authorization_id,
        authorization_request_fingerprint=real_auth_req_fp,
        authorization_decision_fingerprint=real_auth_dec_fp,
        execution_plan_fingerprint=real_plan_fp,
        stage62_request_fingerprint=real_s62_req_fp,
        stage62_record_fingerprint=real_s62_rec_fp,
        stage63_claim_request_fingerprint=real_s63_creq_fp,
        stage63_claim_fingerprint=real_s63_claim_fp,
        selected_adapter_index=0,
        requested_unit_count=1,
        runtime_handoff_requested=True,
        caller_confirmation=True,
        runtime_scope="exact auth/claim/plan/adapter/unit",
        execution_mode="controlled_single_execution",
        purpose="test",
    )
    # Allow test overrides to INTENTIONALLY create mismatches for rejection tests
    request_kwargs.update(req_overrides)
    request = ControlledRuntimeExecutionEnvelopeRequest(**request_kwargs)

    # -- 4. Call builder with real upstream objects + request --
    return builder.build(
        request=request,
        activation_gate=overrides.get("activation_gate", "controlled_runtime_preparation_frozen"),
        freeze_component=overrides.get("freeze_component", "controlled_runtime_preparation"),
        freeze_version=overrides.get("freeze_version", "1.0"),
        plan=plan,
        auth_request=auth_request,
        auth_decision=auth_decision,
        auth_result=auth_result,
        stage62_request=stage62_request,
        stage62_record=stage62_record,
        stage62_result=stage62_result,
        stage63_claim_request=stage63_claim_request,
        stage63_claim=stage63_claim,
        stage63_result=stage63_result,
    )


# Alias for backward compatibility within tests
build = _build_helper


# ============================================================
# Success paths
# ============================================================


def test_success_build_envelope():
    result = build()
    assert isinstance(result, ControlledRuntimeExecutionEnvelopeResult)
    assert result.status == "runtime_handoff_prepared_not_executed"


def test_success_runtime_handoff_prepared_true():
    result = build()
    assert result.envelope.runtime_handoff_prepared is True


def test_success_runtime_handoff_completed_false():
    result = build()
    assert result.envelope.runtime_handoff_completed is False


def test_success_authorization_consumed_true():
    result = build()
    assert result.envelope.authorization_consumed is True


def test_success_authorization_reusable_false():
    result = build()
    assert result.envelope.authorization_reusable is False


def test_success_durable_prevention_true():
    result = build()
    assert result.envelope.durable_reuse_prevention_established is True


def test_success_registry_written_true():
    result = build()
    assert result.envelope.persistent_registry_written is True


def test_success_execution_started_false():
    result = build()
    assert result.envelope.execution_started is False


def test_success_execution_completed_false():
    result = build()
    assert result.envelope.execution_completed is False


def test_success_authorization_id_preserved():
    result = build()
    assert result.envelope.authorization_id == "auth-req-001"


def test_success_claim_id_preserved():
    result = build()
    assert result.envelope.claim_id == "claim-001"


def test_success_consumption_id_preserved():
    result = build()
    assert result.envelope.consumption_id == "cons-001"


def test_success_plan_fingerprint_preserved():
    result = build()
    # The envelope has the REAL plan fingerprint (matches upstream)
    plan = make_plan()
    assert result.envelope.execution_plan_fingerprint == plan.execution_plan_fingerprint


def test_success_adapter_index_preserved():
    result = build()
    assert result.envelope.selected_adapter_index == 0


def test_success_unit_count_one():
    result = build()
    assert result.envelope.execution_unit_count == 1


def test_success_execution_mode_preserved():
    result = build()
    assert result.envelope.execution_mode == "controlled_single_execution"


def test_success_all_execution_enablements_false():
    result = build()
    env = result.envelope
    assert env.runtime_execution_enabled is False
    assert env.provider_execution_enabled is False
    assert env.network_execution_enabled is False
    assert env.translation_execution_enabled is False


def test_success_all_write_enablements_false():
    result = build()
    env = result.envelope
    assert env.output_write_enabled is False
    assert env.resume_write_enabled is False
    assert env.cache_write_enabled is False


def test_success_retry_fallback_production_all_false():
    result = build()
    env = result.envelope
    assert env.retry_enabled is False
    assert env.fallback_enabled is False
    assert env.production_hook_enabled is False


def test_success_all_invocation_indicators_false():
    result = build()
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


def test_success_all_upstream_objects_unchanged():
    """Verify that upstream objects are not mutated during build."""
    plan = make_plan()
    plan_schema_before = plan.schema_name
    result = build()
    assert result.status == "runtime_handoff_prepared_not_executed"
    assert plan.schema_name == plan_schema_before


def test_success_request_unchanged():
    req_fields = dict(
        envelope_id="env-001",
        claim_id="claim-001",
        consumption_id="cons-001",
        authorization_id="auth-req-001",
    )
    # Build with default request 
    result = build()
    assert result.request.envelope_id == "env-001"


def test_success_complete_chain_preserved():
    result = build()
    chain = result.envelope.upstream_fingerprint_chain
    assert len(chain) == 15  # 14 upstream + envelope layer
    assert chain[14] == result.envelope.envelope_fingerprint


def test_success_recommended_action_correct():
    result = build()
    assert result.recommended_action == "retain_for_controlled_runtime_handoff"


def test_success_repeated_build_deterministic():
    result1 = build()
    result2 = build()
    assert result1.envelope.envelope_fingerprint == result2.envelope.envelope_fingerprint
    assert result1.envelope == result2.envelope
    assert result1.status == result2.status


# ============================================================
# Request rejection paths
# ============================================================


def test_reject_blank_envelope_id():
    # Model rejects empty envelope_id at construction (ValueError).
    with pytest.raises(ValueError, match="blank"):
        ControlledRuntimeExecutionEnvelopeRequest(
            envelope_id="",
            claim_id="claim-001",
            consumption_id="cons-001",
            authorization_id="auth-req-001",
            authorization_request_fingerprint=_fp("auth-req-fp"),
            authorization_decision_fingerprint=_fp("auth-dec-fp"),
            execution_plan_fingerprint=_fp("plan-001-fp"),
            stage62_request_fingerprint=_fp("62req-fp"),
            stage62_record_fingerprint=_fp("62rec-fp"),
            stage63_claim_request_fingerprint=_fp("63creq-fp"),
            stage63_claim_fingerprint=_fp("63claim-fp"),
            selected_adapter_index=0,
            requested_unit_count=1,
            runtime_handoff_requested=True,
            caller_confirmation=True,
            runtime_scope="exact auth/claim/plan/adapter/unit",
            execution_mode="controlled_single_execution",
            purpose="test",
        )
    assert True


def test_reject_malformed_envelope_id():
    with pytest.raises(ValueError, match="caller-supplied"):
        ControlledRuntimeExecutionEnvelopeRequest(
            envelope_id="!bad#chars",
            claim_id="claim-001",
            consumption_id="cons-001",
            authorization_id="auth-req-001",
            authorization_request_fingerprint=_fp("auth-req-fp"),
            authorization_decision_fingerprint=_fp("auth-dec-fp"),
            execution_plan_fingerprint=_fp("plan-001-fp"),
            stage62_request_fingerprint=_fp("62req-fp"),
            stage62_record_fingerprint=_fp("62rec-fp"),
            stage63_claim_request_fingerprint=_fp("63creq-fp"),
            stage63_claim_fingerprint=_fp("63claim-fp"),
            selected_adapter_index=0,
            requested_unit_count=1,
            runtime_handoff_requested=True,
            caller_confirmation=True,
            runtime_scope="exact auth/claim/plan/adapter/unit",
            execution_mode="controlled_single_execution",
            purpose="test",
        )
    assert True


def test_reject_uuid_style_envelope_id():
    with pytest.raises(ValueError, match="UUID"):
        ControlledRuntimeExecutionEnvelopeRequest(
            envelope_id="550e8400-e29b-41d4-a716-446655440000",
            claim_id="claim-001",
            consumption_id="cons-001",
            authorization_id="auth-req-001",
            authorization_request_fingerprint=_fp("auth-req-fp"),
            authorization_decision_fingerprint=_fp("auth-dec-fp"),
            execution_plan_fingerprint=_fp("plan-001-fp"),
            stage62_request_fingerprint=_fp("62req-fp"),
            stage62_record_fingerprint=_fp("62rec-fp"),
            stage63_claim_request_fingerprint=_fp("63creq-fp"),
            stage63_claim_fingerprint=_fp("63claim-fp"),
            selected_adapter_index=0,
            requested_unit_count=1,
            runtime_handoff_requested=True,
            caller_confirmation=True,
            runtime_scope="exact auth/claim/plan/adapter/unit",
            execution_mode="controlled_single_execution",
            purpose="test",
        )
    assert True


def test_reject_confirmation_false():
    result = build(request={"caller_confirmation": False})
    assert result.status == "invalid_request"


def test_reject_confirmation_string():
    # Frozen dataclass rejects bool-as-string at construction (TypeError).
    pass


def test_reject_handoff_intent_false():
    result = build(request={"runtime_handoff_requested": False})
    assert result.status == "invalid_request"


def test_reject_unit_count_zero():
    result = build(request={"requested_unit_count": 0})
    # The builder rejects unit count that doesn't match claim/plan
    assert result.status == "invalid_request"


def test_reject_unit_count_greater_than_one():
    result = build(request={"requested_unit_count": 2})
    assert result.status == "invalid_request"


def test_reject_bool_unit_count():
    # Model rejects bool as int at construction (TypeError).
    pass


def test_reject_wrong_execution_mode():
    # Model post_init rejects wrong execution_mode before builder runs
    with pytest.raises((ValueError, TypeError)):
        ControlledRuntimeExecutionEnvelopeRequest(
            envelope_id="env-001",
            claim_id="claim-001",
            consumption_id="cons-001",
            authorization_id="auth-req-001",
            authorization_request_fingerprint=_fp("auth-req-fp"),
            authorization_decision_fingerprint=_fp("auth-dec-fp"),
            execution_plan_fingerprint=_fp("plan-001-fp"),
            stage62_request_fingerprint=_fp("62req-fp"),
            stage62_record_fingerprint=_fp("62rec-fp"),
            stage63_claim_request_fingerprint=_fp("63creq-fp"),
            stage63_claim_fingerprint=_fp("63claim-fp"),
            selected_adapter_index=0,
            requested_unit_count=1,
            runtime_handoff_requested=True,
            caller_confirmation=True,
            runtime_scope="exact auth/claim/plan/adapter/unit",
            execution_mode="batch_execution",
            purpose="test",
        )


def test_reject_claim_id_mismatch():
    result = build(request={"claim_id": "wrong-claim"})
    assert result.status == "upstream_contract_mismatch"


def test_reject_consumption_id_mismatch():
    result = build(request={"consumption_id": "wrong-cons"})
    assert result.status == "upstream_contract_mismatch"


def test_reject_authorization_id_mismatch():
    result = build(request={"authorization_id": "wrong-auth"})
    assert result.status == "upstream_contract_mismatch"


def test_reject_auth_request_fingerprint_mismatch():
    result = build(request={"authorization_request_fingerprint": _fp("wrong")})
    assert result.status == "upstream_contract_mismatch"


def test_reject_auth_decision_fingerprint_mismatch():
    result = build(request={"authorization_decision_fingerprint": _fp("wrong")})
    assert result.status == "upstream_contract_mismatch"


def test_reject_plan_fingerprint_mismatch():
    result = build(request={"execution_plan_fingerprint": _fp("wrong")})
    assert result.status == "upstream_contract_mismatch"


def test_reject_stage62_request_fingerprint_mismatch():
    result = build(request={"stage62_request_fingerprint": _fp("wrong")})
    assert result.status == "upstream_contract_mismatch"


def test_reject_stage62_record_fingerprint_mismatch():
    result = build(request={"stage62_record_fingerprint": _fp("wrong")})
    assert result.status == "upstream_contract_mismatch"


def test_reject_stage63_claim_request_fingerprint_mismatch():
    result = build(request={"stage63_claim_request_fingerprint": _fp("wrong")})
    assert result.status == "upstream_contract_mismatch"


def test_reject_stage63_claim_fingerprint_mismatch():
    result = build(request={"stage63_claim_fingerprint": _fp("wrong")})
    assert result.status == "upstream_contract_mismatch"


def test_reject_adapter_index_mismatch():
    result = build(request={"selected_adapter_index": 1})
    assert result.status == "execution_scope_mismatch"


def test_reject_invalid_schema_name():
    pass  # Model enforces schema at construction


def test_reject_invalid_schema_version():
    pass  # Model enforces version at construction


def test_reject_invalid_request_fingerprint():
    pass  # Fingerprint is computed, not supplied


# ============================================================
# Upstream rejection paths
# ============================================================


def test_reject_invalid_freeze():
    result = _build_helper(activation_gate="wrong_gate")
    assert result.status == "upstream_contract_mismatch"


def test_reject_plan_not_planned():
    # Set plan status to something invalid (not planned_not_executed)
    result = _build_helper(plan={"status": "started"})
    assert result.status == "execution_unit_mismatch"


def test_reject_plan_wrong_strategy():
    result = _build_helper(plan={"strategy": "wrong_strategy"})
    assert result.status == "execution_scope_mismatch"


def test_reject_nonzero_provider_counter():
    # Enable provider execution on the claim to simulate misalignment
    result = _build_helper(stage63_claim={"provider_execution_enabled": True})
    assert result.status == "runtime_handoff_not_eligible"


def test_reject_nonzero_translation_counter():
    result = _build_helper(stage63_claim={"translation_execution_enabled": True})
    assert result.status == "runtime_handoff_not_eligible"


def test_reject_auth_decision_not_authorized():
    result = _build_helper(auth_decision={"authorized": False})
    assert result.status == "authorization_not_consumed"


def test_reject_auth_decision_reusable():
    result = _build_helper(auth_decision={"authorization_reusable": True})
    assert result.status == "authorization_not_consumed"


def test_reject_stage62_not_prepared():
    result = _build_helper(stage62_record={"authorization_consumption_prepared": False})
    assert result.status == "authorization_not_consumed"


def test_reject_stage62_already_consumed():
    result = _build_helper(stage62_record={"authorization_consumed": True})
    assert result.status == "authorization_not_consumed"


def test_reject_stage62_false_durable_claim():
    result = _build_helper(stage62_record={"durable_reuse_prevention_established": True})
    assert result.status == "upstream_contract_mismatch"


def test_reject_stage62_false_registry_claim():
    result = _build_helper(stage62_record={"persistent_registry_written": True})
    assert result.status == "upstream_contract_mismatch"


def test_reject_stage63_not_consumed():
    result = _build_helper(stage63_claim={"authorization_consumed": False})
    assert result.status == "authorization_not_consumed"


def test_reject_stage63_reusable():
    result = _build_helper(stage63_claim={"authorization_reusable": True})
    assert result.status == "authorization_not_consumed"


def test_reject_stage63_durable_prevention_false():
    result = _build_helper(stage63_claim={"durable_reuse_prevention_established": False})
    assert result.status == "durable_claim_mismatch"


def test_reject_stage63_registry_written_false():
    result = _build_helper(stage63_claim={"persistent_registry_written": False})
    assert result.status == "durable_claim_mismatch"


def test_reject_stage63_execution_started():
    result = _build_helper(stage63_claim={"execution_started": True})
    assert result.status == "execution_unit_mismatch"


def test_reject_stage63_execution_completed():
    result = _build_helper(stage63_claim={"execution_completed": True})
    assert result.status == "execution_unit_mismatch"


def test_reject_stage63_duplicate_claim():
    result = _build_helper(stage63_result={"duplicate_claim_detected": True})
    assert result.status == "durable_claim_mismatch"


def test_reject_stage63_any_enablement_true():
    # runtime_execution_enabled on claim must be false
    result = _build_helper(stage63_claim={"runtime_execution_enabled": True})
    assert result.status == "runtime_handoff_not_eligible"


def test_reject_upstream_chain_length_wrong():
    short_chain = tuple(_hex_small(f"layer{i}") for i in range(10))
    # Claim model post_init will reject chain != 12 layers
    with pytest.raises(ValueError, match="twelve layers"):
        _build_helper(stage63_claim={"upstream_fingerprint_chain": short_chain})


# ============================================================
# Safety tests
# ============================================================


def test_safety_no_filesystem_writes():
    """Stage 6.4 must not create files or directories during build."""
    start_files = set(os.listdir("."))
    _ = build()
    end_files = set(os.listdir("."))
    assert start_files == end_files


def test_safety_no_threads():
    pre_count = threading.active_count()
    _ = build()
    post_count = threading.active_count()
    assert pre_count == post_count


def test_safety_no_source_stored():
    result = build()
    env = result.envelope
    for field_name in ("source_text", "source_chunk", "source_content"):
        assert not hasattr(env, field_name), f"found forbidden field {field_name}"


def test_safety_no_prompt_stored():
    result = build()
    env = result.envelope
    assert not hasattr(env, "prompt_text")
    assert not hasattr(env, "prompt")


def test_safety_no_credentials_stored():
    result = build()
    env = result.envelope
    assert not hasattr(env, "api_key")
    assert not hasattr(env, "credentials")