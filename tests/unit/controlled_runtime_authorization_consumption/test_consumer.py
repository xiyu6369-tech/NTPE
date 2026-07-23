"""Unit tests for ControlledRuntimeAuthorizationConsumer.

Tests: success-eligible consumption preparation and mandatory rejections.
Does not test upstream verification exhaustively (that belongs to upstream tests).
Uses minimal valid upstream models built from public constructors.

When the consumer requires freeze-gate validation, we inject a success mock;
all other validation uses real upstream verifiers.
"""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import FrozenInstanceError, fields, replace
from hashlib import sha256
from unittest.mock import MagicMock

import pytest

from core.controlled_runtime_authorization_consumption import (
    ControlledRuntimeAuthorizationConsumer,
)
from core.controlled_runtime_authorization_consumption.errors import (
    ControlledRuntimeAuthorizationConsumptionError,
)
from core.controlled_runtime_authorization_consumption.models import (
    CONSUMPTION_REQUEST_SCHEMA_NAME,
    CONSUMPTION_REQUEST_SCHEMA_VERSION,
    ControlledRuntimeAuthorizationConsumptionRecord,
    ControlledRuntimeAuthorizationConsumptionRequest,
)
from core.controlled_runtime_authorization_consumption.policy import (
    exact_consumption_scope,
)
from core.controlled_runtime_authorization_consumption.verification import (
    verify_consumption_record,
)
from core.controlled_runtime_execution_authorization import (
    ControlledRuntimeExecutionAuthorizationDecision,
    ControlledRuntimeExecutionAuthorizationRequest,
)
from core.controlled_runtime_execution_plan import (
    ControlledRuntimeExecutionPolicy,
    ControlledRuntimeExecutionPlan,
    ControlledRuntimeExecutionSourceReference,
    ControlledRuntimeExecutionStep,
    get_controlled_runtime_preparation_freeze_metadata,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_HEX64 = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


def _fake_sha256(seed: str) -> str:
    """Return a deterministic 64-char hex fingerprint."""
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _make_source() -> ControlledRuntimeExecutionSourceReference:
    return ControlledRuntimeExecutionSourceReference(
        source_name="test-source",
        source_content_fingerprint=_fake_sha256("content"),
        execution_package_fingerprint=_fake_sha256("package"),
        authorization_fingerprint=_fake_sha256("auth"),
        approval_record_fingerprint=_fake_sha256("approval"),
        runtime_submission_package_fingerprint=_fake_sha256("submission-pkg"),
        runtime_adapter_request_fingerprint=_fake_sha256("adapter-req"),
        runtime_adapter_preparation_fingerprint=_fake_sha256("adapter-prep"),
        manifest_fingerprint=_fake_sha256("manifest"),
        segmentation_fingerprint=_fake_sha256("segmentation"),
        chunk_plan_fingerprint=_fake_sha256("chunk-plan"),
        preparation_fingerprint=_fake_sha256("preparation"),
    )


def _make_policy() -> ControlledRuntimeExecutionPolicy:
    return ControlledRuntimeExecutionPolicy(
        policy_name="test-policy",
        policy_version="1.0",
        execution_mode="strict_single_unit",
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


def _make_step(
    index: int = 0,
    text: str = "test-text-content-0000",
) -> ControlledRuntimeExecutionStep:
    return ControlledRuntimeExecutionStep(
        step_index=index,
        adapter_unit_index=index,
        submission_index=index,
        execution_unit_index=index,
        execution_unit_id=f"unit-{index}",
        text=text,
        source_character_start=0,
        source_character_end=len(text),
        section_indices=(),
        source_chunk_fingerprint=_fake_sha256(f"chunk-{index}"),
        execution_unit_fingerprint=_fake_sha256(f"eu-{index}"),
        runtime_submission_unit_fingerprint=_fake_sha256(f"sub-unit-{index}"),
        runtime_adapter_unit_fingerprint=_fake_sha256(f"adapter-unit-{index}"),
        planned_provider_request_limit=1,
        planned_retry_limit=0,
        planned_fallback_limit=0,
        status="planned_not_executed",
        runtime_attempt_count=0,
        provider_request_count=0,
        translation_result_attached=False,
        execution_step_fingerprint=_fake_sha256(f"step-fp-{index}"),
    )


def _make_valid_plan(
    *,
    selected_adapter_unit_indices: tuple[int, ...] = (0,),
) -> ControlledRuntimeExecutionPlan:
    source = _make_source()
    policy = _make_policy()
    steps = tuple(
        _make_step(index=idx) for idx in selected_adapter_unit_indices
    )
    return ControlledRuntimeExecutionPlan(
        schema_name="ntpe.controlled_runtime_execution_plan",
        schema_version="1.0",
        strategy="one_unit_no_overlap",
        activation_gate="controlled_runtime_preparation_frozen",
        source=source,
        policy=policy,
        steps=steps,
        selected_adapter_unit_indices=selected_adapter_unit_indices,
        planned_step_count=len(steps),
        available_adapter_unit_count=1,
        planned_character_count=sum(len(s.text) for s in steps),
        approved_character_count=sum(len(s.text) for s in steps),
        planned_approval_coverage_ratio=1.0,
        status="planned_not_executed",
        action="hold",
        findings=(),
        summary="test plan",
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
        execution_plan_fingerprint=_fake_sha256("plan"),
    )


def _build_plan():
    """Build a minimal valid plan returning its fingerprint."""
    plan = _make_valid_plan()
    return plan


def _make_valid_auth_request(
    plan_fingerprint: str,
) -> ControlledRuntimeExecutionAuthorizationRequest:
    return ControlledRuntimeExecutionAuthorizationRequest(
        authorization_id=_fake_sha256("auth-id"),
        execution_plan_fingerprint=plan_fingerprint,
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
        authorization_scope=(
            f"plan:{plan_fingerprint}:unit:0:provider:1:translation:1"
            ":retry:0:fallback:0"
        ),
        purpose="stage-6.2-test",
        schema_name="ntpe.controlled_runtime_execution_authorization_request",
        schema_version="1.0",
        requested_unit_count=1,
    )


def _make_valid_auth_decision(
    plan_fingerprint: str,
    auth_request_fingerprint: str,
) -> ControlledRuntimeExecutionAuthorizationDecision:
    return ControlledRuntimeExecutionAuthorizationDecision(
        authorization_id=_fake_sha256("auth-id"),
        authorized=True,
        status="authorized_not_executed",
        reason_codes=(),
        execution_package_fingerprint=_fake_sha256("package"),
        upstream_authorization_decision_fingerprint=_fake_sha256(
            "upstream-auth-dec"
        ),
        approval_record_fingerprint=_fake_sha256("approval"),
        runtime_submission_package_fingerprint=_fake_sha256("submission-pkg"),
        runtime_adapter_request_fingerprint=_fake_sha256("adapter-req"),
        runtime_adapter_preparation_fingerprint=_fake_sha256("adapter-prep"),
        authorization_request_fingerprint=auth_request_fingerprint,
        authorized_execution_plan_fingerprint=plan_fingerprint,
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
        decision_fingerprint="",  # computed by __post_init__
        schema_name="ntpe.controlled_runtime_execution_authorization_decision",
        schema_version="1.0",
    )


def _make_success_consumer() -> ControlledRuntimeAuthorizationConsumer:
    """Return a consumer whose freeze gate always passes."""
    mock_result = MagicMock()
    mock_result.valid = True
    return ControlledRuntimeAuthorizationConsumer(
        freeze_validator=lambda: mock_result,
    )


def _make_setup():
    """Create minimal but valid models for a success-eligible preparation."""
    plan = _make_valid_plan()
    auth_req = _make_valid_auth_request(plan.execution_plan_fingerprint)
    auth_dec = _make_valid_auth_decision(
        plan.execution_plan_fingerprint,
        auth_req.request_fingerprint,
    )
    freeze_meta = get_controlled_runtime_preparation_freeze_metadata()
    consumer = _make_success_consumer()
    return plan, auth_req, auth_dec, freeze_meta, consumer


def _make_valid_consumption_request(
    auth_req_fp: str,
    auth_dec_fp: str,
    plan_fp: str,
) -> ControlledRuntimeAuthorizationConsumptionRequest:
    return ControlledRuntimeAuthorizationConsumptionRequest(
        consumption_id="stage-6.2-test-consumption-001",
        authorization_id=_fake_sha256("auth-id"),
        authorization_request_fingerprint=auth_req_fp,
        authorization_decision_fingerprint=auth_dec_fp,
        execution_plan_fingerprint=plan_fp,
        selected_adapter_index=0,
        requested_unit_count=1,
        consume_for_single_execution=True,
        caller_confirmation=True,
        consumption_scope=exact_consumption_scope(
            _fake_sha256("auth-id"),
            auth_req_fp,
            auth_dec_fp,
            plan_fp,
            0,
            1,
        ),
        purpose="stage-6.2-test",
        schema_name=CONSUMPTION_REQUEST_SCHEMA_NAME,
        schema_version=CONSUMPTION_REQUEST_SCHEMA_VERSION,
    )


# ---------------------------------------------------------------------------
# Successful preparation
# ---------------------------------------------------------------------------


def test_prepare_consumption_success():
    """Authentic Stage 6.1 authorization prepares consumption."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status == "consumption_prepared_not_executed"
    assert result.freeze_gate_verified is True
    assert result.execution_plan_verified is True
    assert result.authorization_request_verified is True
    assert result.authorization_decision_verified is True
    assert result.authorization_binding_verified is True
    assert result.prior_consumption_state_verified is True


def test_record_status_on_success():
    """Record status is consumption_prepared_not_executed."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.record.status == "consumption_prepared_not_executed"


def test_authorization_consumption_prepared_true():
    """Record shows authorization_consumption_prepared = true."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.record.authorization_consumption_prepared is True


def test_authorization_consumed_remains_false():
    """Record shows authorization_consumed = false."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.record.authorization_consumed is False


def test_authorization_reusable_remains_false():
    """Record shows authorization_reusable = false."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.record.authorization_reusable is False


def test_durable_reuse_prevention_false():
    """Record shows durable_reuse_prevention_established = false."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.record.durable_reuse_prevention_established is False


def test_persistent_registry_written_false():
    """Record shows persistent_registry_written = false."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.record.persistent_registry_written is False


def test_execution_started_false():
    """Record shows execution_started = false."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.record.execution_started is False


def test_execution_completed_false():
    """Record shows execution_completed = false."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.record.execution_completed is False


def test_exact_authorization_id_preserved():
    """Record preserves exact authorization ID."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.record.authorization_id == _fake_sha256("auth-id")


def test_exact_request_fingerprint_preserved():
    """Record preserves exact authorization request fingerprint."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert (
        result.record.authorization_request_fingerprint
        == auth_req.request_fingerprint
    )


def test_exact_decision_fingerprint_preserved():
    """Record preserves exact authorization decision fingerprint."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert (
        result.record.authorization_decision_fingerprint
        == auth_dec.decision_fingerprint
    )


def test_exact_plan_fingerprint_preserved():
    """Record preserves exact execution plan fingerprint."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert (
        result.record.execution_plan_fingerprint
        == plan.execution_plan_fingerprint
    )


def test_exact_adapter_index_preserved():
    """Record preserves exact adapter index."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.record.selected_adapter_index == 0


def test_consumed_unit_count_exactly_one():
    """Record shows consumed_unit_count = 1."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.record.consumed_unit_count == 1


def test_upstream_chain_preserved():
    """Record preserves the full upstream fingerprint chain (11 layers)."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    chain = result.record.upstream_fingerprint_chain
    assert len(chain) == 11
    assert chain[10] == result.record.record_fingerprint


def test_all_enablement_remains_false():
    """Record shows all execution enablement fields = false."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    r = result.record
    assert r.runtime_execution_enabled is False
    assert r.provider_execution_enabled is False
    assert r.network_execution_enabled is False
    assert r.translation_execution_enabled is False
    assert r.output_write_enabled is False
    assert r.resume_write_enabled is False
    assert r.cache_write_enabled is False
    assert r.retry_enabled is False
    assert r.fallback_enabled is False
    assert r.production_hook_enabled is False


def test_all_invocation_indicators_false():
    """Result shows all invocation indicators = false."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
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


def test_plan_unchanged_after_preparation():
    """Stage 5 plan remains unchanged after consumption preparation."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    plan_copy = copy.deepcopy(plan)
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert (
        plan.execution_plan_fingerprint
        == plan_copy.execution_plan_fingerprint
    )
    assert plan.status == plan_copy.status
    assert plan.execution_started == plan_copy.execution_started
    assert plan.execution_completed == plan_copy.execution_completed


def test_auth_request_unchanged_after_preparation():
    """Stage 6.1 authorization request remains unchanged."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    fp_before = auth_req.request_fingerprint
    consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert auth_req.request_fingerprint == fp_before


def test_auth_decision_unchanged_after_preparation():
    """Stage 6.1 authorization decision remains unchanged."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    fp_before = auth_dec.decision_fingerprint
    consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert auth_dec.decision_fingerprint == fp_before


def test_consumption_request_unchanged_after_preparation():
    """Stage 6.2 consumption request remains unchanged."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    fp_before = req.request_fingerprint
    consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert req.request_fingerprint == fp_before


# ---------------------------------------------------------------------------
# Request rejection
# ---------------------------------------------------------------------------


def test_blank_consumption_id_rejected():
    """Blank consumption ID is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = replace(
        _make_valid_consumption_request(
            auth_req.request_fingerprint,
            auth_dec.decision_fingerprint,
            plan.execution_plan_fingerprint,
        ),
        consumption_id="",
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_malformed_consumption_id_rejected():
    """Malformed consumption ID is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = replace(
        _make_valid_consumption_request(
            auth_req.request_fingerprint,
            auth_dec.decision_fingerprint,
            plan.execution_plan_fingerprint,
        ),
        consumption_id="\x00\x01",
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_confirmation_false_rejected():
    """False caller_confirmation is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = replace(
        _make_valid_consumption_request(
            auth_req.request_fingerprint,
            auth_dec.decision_fingerprint,
            plan.execution_plan_fingerprint,
        ),
        caller_confirmation=False,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_single_execution_intent_false_rejected():
    """consume_for_single_execution = false is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = replace(
        _make_valid_consumption_request(
            auth_req.request_fingerprint,
            auth_dec.decision_fingerprint,
            plan.execution_plan_fingerprint,
        ),
        consume_for_single_execution=False,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_authorization_id_mismatch_rejected():
    """Authorization ID mismatch is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = replace(
        _make_valid_consumption_request(
            auth_req.request_fingerprint,
            auth_dec.decision_fingerprint,
            plan.execution_plan_fingerprint,
        ),
        authorization_id=_fake_sha256("wrong-auth-id"),
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_authorization_request_fingerprint_mismatch_rejected():
    """Authorization request fingerprint mismatch is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = replace(
        _make_valid_consumption_request(
            auth_req.request_fingerprint,
            auth_dec.decision_fingerprint,
            plan.execution_plan_fingerprint,
        ),
        authorization_request_fingerprint=_fake_sha256("wrong"),
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_authorization_decision_fingerprint_mismatch_rejected():
    """Authorization decision fingerprint mismatch is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = replace(
        _make_valid_consumption_request(
            auth_req.request_fingerprint,
            auth_dec.decision_fingerprint,
            plan.execution_plan_fingerprint,
        ),
        authorization_decision_fingerprint=_fake_sha256("wrong"),
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_execution_plan_fingerprint_mismatch_rejected():
    """Execution plan fingerprint mismatch is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = replace(
        _make_valid_consumption_request(
            auth_req.request_fingerprint,
            auth_dec.decision_fingerprint,
            plan.execution_plan_fingerprint,
        ),
        execution_plan_fingerprint=_fake_sha256("wrong"),
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_adapter_index_mismatch_rejected():
    """Selected adapter index mismatch is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = replace(
        _make_valid_consumption_request(
            auth_req.request_fingerprint,
            auth_dec.decision_fingerprint,
            plan.execution_plan_fingerprint,
        ),
        selected_adapter_index=9,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_zero_unit_count_rejected():
    """Requested unit count 0 is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = replace(
        _make_valid_consumption_request(
            auth_req.request_fingerprint,
            auth_dec.decision_fingerprint,
            plan.execution_plan_fingerprint,
        ),
        requested_unit_count=0,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_unit_count_greater_than_one_rejected():
    """Requested unit count > 1 is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = replace(
        _make_valid_consumption_request(
            auth_req.request_fingerprint,
            auth_dec.decision_fingerprint,
            plan.execution_plan_fingerprint,
        ),
        requested_unit_count=2,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_invalid_request_schema_rejected():
    """Wrong schema name is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    base = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    # Bypass __post_init__ validation to create invalid schema
    object.__setattr__(base, "schema_name", "wrong.schema")
    # Recompute fingerprint with tampered schema
    payload = {f.name: getattr(base, f.name) for f in fields(base) if f.name not in ("request_fingerprint",)}
    object.__setattr__(base, "request_fingerprint", sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest())
    result = consumer.prepare_consumption(
        request=base,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_invalid_request_version_rejected():
    """Wrong schema version is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    base = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    # Bypass __post_init__ validation to create invalid schema version
    object.__setattr__(base, "schema_version", "99.0")
    # Recompute fingerprint with tampered version
    payload = {f.name: getattr(base, f.name) for f in fields(base) if f.name not in ("request_fingerprint",)}
    object.__setattr__(base, "request_fingerprint", sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest())
    result = consumer.prepare_consumption(
        request=base,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_invalid_request_fingerprint_rejected():
    """Tampered consumption request fingerprint fails."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    # Use object.__setattr__ to bypass frozen protection (simulating tampering)
    object.__setattr__(
        req, "request_fingerprint", _fake_sha256("tampered-fp")
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_tampered_purpose_changes_fingerprint():
    """Tampering purpose changes the request fingerprint."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req1 = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    req2 = replace(req1, purpose="different-purpose")
    assert req1.request_fingerprint != req2.request_fingerprint


def test_tampered_scope_changes_fingerprint():
    """Tampering consumption scope changes the request fingerprint."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req1 = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    req2 = replace(req1, consumption_scope="tampered-scope")
    assert req1.request_fingerprint != req2.request_fingerprint


# ---------------------------------------------------------------------------
# Upstream rejection
# ---------------------------------------------------------------------------


def test_wrong_freeze_gate_rejected():
    """Failing freeze gate rejects preparation."""
    plan, auth_req, auth_dec, _freeze_meta, _consumer = _make_setup()
    freeze_meta = get_controlled_runtime_preparation_freeze_metadata()
    # Build a consumer whose freeze gate fails
    mock_result = MagicMock()
    mock_result.valid = False
    consumer = ControlledRuntimeAuthorizationConsumer(
        freeze_validator=lambda: mock_result,
    )
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"
    assert result.freeze_gate_verified is False


def test_missing_freeze_metadata_rejected():
    """None freeze metadata is rejected."""
    plan, auth_req, auth_dec, _freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=None,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_invalid_execution_plan_rejected():
    """An execution plan with invalid schema name is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    bad_plan = replace(plan, schema_name="wrong.schema")
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=bad_plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_plan_already_started_rejected():
    """An execution plan with execution_started=True is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    bad_plan = replace(plan, execution_started=True)
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=bad_plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_plan_already_completed_rejected():
    """An execution plan with execution_completed=True is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    bad_plan = replace(plan, execution_completed=True)
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=bad_plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_wrong_plan_state_rejected():
    """Wrong plan status is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    bad_plan = replace(plan, status="executing")
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=bad_plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_nonzero_provider_counter_rejected():
    """Nonzero provider_requests_executed on plan is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    bad_plan = replace(plan, provider_requests_executed=1)
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=bad_plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_nonzero_translation_counter_rejected():
    """Nonzero translation_executions_completed on plan is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    bad_plan = replace(plan, translation_executions_completed=1)
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=bad_plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_invalid_stage61_request_rejected():
    """Wrong Stage 6.1 request schema is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    bad_req = replace(auth_req, schema_name="wrong.schema")
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=bad_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_invalid_stage61_decision_rejected():
    """Wrong Stage 6.1 decision schema is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    bad_dec = replace(auth_dec, schema_name="wrong.schema")
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=bad_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_rejected_authorization_rejected():
    """authorized=False is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    bad_dec = replace(auth_dec, authorized=False)
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        bad_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=bad_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_wrong_authorization_status_rejected():
    """status != authorized_not_executed is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    bad_dec = replace(auth_dec, status="authorized_and_executed")
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        bad_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=bad_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_authorization_already_consumed_rejected():
    """authorization_consumed=True is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    bad_dec = replace(auth_dec, authorization_consumed=True)
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        bad_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=bad_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_authorization_reusable_true_rejected():
    """authorization_reusable=True is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    bad_dec = replace(auth_dec, authorization_reusable=True)
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        bad_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=bad_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_wrong_provider_limit_rejected():
    """authorized_provider_request_limit != 1 is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    bad_dec = replace(auth_dec, authorized_provider_request_limit=2)
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        bad_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=bad_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_wrong_translation_limit_rejected():
    """authorized_translation_request_limit != 1 is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    bad_dec = replace(auth_dec, authorized_translation_request_limit=2)
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        bad_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=bad_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_nonzero_retry_limit_rejected():
    """authorized_retry_limit > 0 is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    bad_dec = replace(auth_dec, authorized_retry_limit=1)
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        bad_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=bad_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_nonzero_fallback_limit_rejected():
    """authorized_fallback_limit > 0 is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    bad_dec = replace(auth_dec, authorized_fallback_limit=1)
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        bad_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=bad_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_output_replacement_authorized_rejected():
    """output_replacement_authorized=True is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    bad_dec = replace(auth_dec, output_replacement_authorized=True)
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        bad_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=bad_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_production_integration_authorized_rejected():
    """production_integration_authorized=True is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    bad_dec = replace(auth_dec, production_integration_authorized=True)
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        bad_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=bad_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_runtime_enablement_true_rejected():
    """runtime_execution_enabled=True is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    bad_dec = replace(auth_dec, runtime_execution_enabled=True)
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        bad_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=bad_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_provider_enablement_true_rejected():
    """provider_execution_enabled=True is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    bad_dec = replace(auth_dec, provider_execution_enabled=True)
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        bad_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=bad_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_network_enablement_true_rejected():
    """network_execution_enabled=True is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    bad_dec = replace(auth_dec, network_execution_enabled=True)
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        bad_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=bad_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


def test_translation_enablement_true_rejected():
    """translation_execution_enabled=True is rejected."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    bad_dec = replace(auth_dec, translation_execution_enabled=True)
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        bad_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=bad_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.status != "consumption_prepared_not_executed"


# ---------------------------------------------------------------------------
# Truthful durability semantics
# ---------------------------------------------------------------------------


def test_no_persistent_registry_written():
    """No persistent registry is written."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.record.persistent_registry_written is False


def test_no_durable_reuse_prevention_claimed():
    """No durable reuse prevention is claimed."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert result.record.durable_reuse_prevention_established is False


def test_result_recommends_future_atomic_boundary():
    """Result recommends retain_for_atomic_execution_boundary."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert (
        result.recommended_action
        == "retain_for_atomic_execution_boundary"
    )


def test_repeated_evaluation_deterministic():
    """Two consumption preparations with identical inputs yield identical records."""
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result1 = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    result2 = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    assert (
        result1.record.record_fingerprint
        == result2.record.record_fingerprint
    )
    assert result1.status == result2.status


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


def test_result_is_immutable():
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    with pytest.raises(FrozenInstanceError):
        result.status = "modified"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Verification (using the real verify_consumption_record from verification.py)
# ---------------------------------------------------------------------------

def _verification_args(
    record: ControlledRuntimeAuthorizationConsumptionRecord,
    req: ControlledRuntimeAuthorizationConsumptionRequest,
    plan: ControlledRuntimeExecutionPlan,  # noqa: ARG001
) -> dict:
    """Extract the required keyword arguments for verify_consumption_record."""
    return {
        "request_fingerprint": req.request_fingerprint,
        "authorization_id": record.authorization_id,
        "authorization_request_fingerprint": record.authorization_request_fingerprint,
        "authorization_decision_fingerprint": record.authorization_decision_fingerprint,
        "execution_plan_fingerprint": record.execution_plan_fingerprint,
        "adapter_index": record.selected_adapter_index,
        "unit_count": record.consumed_unit_count,
    }


def test_authentic_record_verifies():
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    kwargs = _verification_args(result.record, req, plan)
    verify_consumption_record(result.record, **kwargs)  # must not raise


def test_tampered_record_fingerprint_fails():
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    tampered = replace(result.record, consumed_unit_count=1)  # shallow copy with same payload
    object.__setattr__(tampered, "record_fingerprint", _fake_sha256("tampered-rec"))
    kwargs = _verification_args(tampered, req, plan)
    vr = verify_consumption_record(tampered, **kwargs)
    assert vr.valid is False, "Tampered record fingerprint should fail verification"


def test_tampered_authorization_binding_fails():
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    tampered = replace(result.record, authorization_id=_fake_sha256("wrong"))
    kwargs = _verification_args(tampered, req, plan)
    vr = verify_consumption_record(tampered, **kwargs)
    assert vr.valid is False, "Tampered authorization binding should fail verification"


def test_tampered_plan_binding_fails():
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    tampered = replace(
        result.record,
        execution_plan_fingerprint=_fake_sha256("wrong-plan"),
    )
    kwargs = _verification_args(tampered, req, plan)
    vr = verify_consumption_record(tampered, **kwargs)
    assert vr.valid is False, "Tampered plan binding should fail verification"


def test_tampered_adapter_index_fails():
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    tampered = replace(result.record, selected_adapter_index=99)
    kwargs = _verification_args(tampered, req, plan)
    vr = verify_consumption_record(tampered, **kwargs)
    assert vr.valid is False, "Tampered adapter index should fail verification"


def test_tampered_unit_count_fails():
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    tampered = replace(result.record, consumed_unit_count=2)
    kwargs = _verification_args(tampered, req, plan)
    vr = verify_consumption_record(tampered, **kwargs)
    assert vr.valid is False, "Tampered unit count should fail verification"


def test_tampered_upstream_chain_fails():
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    tampered_chain = tuple(
        list(result.record.upstream_fingerprint_chain[:-1])
        + [_fake_sha256("tampered-link")]
    )
    tampered = replace(
        result.record,
        upstream_fingerprint_chain=tampered_chain,
    )
    kwargs = _verification_args(tampered, req, plan)
    vr = verify_consumption_record(tampered, **kwargs)
    assert vr.valid is False, "Tampered upstream chain should fail verification"


def test_false_execution_claim_fails():
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    tampered = replace(
        result.record,
        execution_started=True,
        execution_completed=True,
    )
    kwargs = _verification_args(tampered, req, plan)
    vr = verify_consumption_record(tampered, **kwargs)
    assert vr.valid is False, "False execution start/completed claim should fail verification"


def test_false_persistent_registry_claim_fails():
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    tampered = replace(
        result.record,
        persistent_registry_written=True,
    )
    kwargs = _verification_args(tampered, req, plan)
    vr = verify_consumption_record(tampered, **kwargs)
    assert vr.valid is False, "False persistent_registry_written claim should fail verification"


def test_false_durable_prevention_claim_fails():
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    tampered = replace(
        result.record,
        durable_reuse_prevention_established=True,
    )
    kwargs = _verification_args(tampered, req, plan)
    vr = verify_consumption_record(tampered, **kwargs)
    assert vr.valid is False, "False durable_reuse_prevention_established claim should fail verification"


def test_enabled_runtime_field_fails():
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    tampered = replace(
        result.record,
        runtime_execution_enabled=True,
    )
    kwargs = _verification_args(tampered, req, plan)
    vr = verify_consumption_record(tampered, **kwargs)
    assert vr.valid is False, "Enabled runtime field should fail verification"


def test_enabled_provider_field_fails():
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    tampered = replace(
        result.record,
        provider_execution_enabled=True,
    )
    kwargs = _verification_args(tampered, req, plan)
    vr = verify_consumption_record(tampered, **kwargs)
    assert vr.valid is False, "Enabled provider field should fail verification"


def test_enabled_network_field_fails():
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    tampered = replace(
        result.record,
        network_execution_enabled=True,
    )
    kwargs = _verification_args(tampered, req, plan)
    vr = verify_consumption_record(tampered, **kwargs)
    assert vr.valid is False, "Enabled network field should fail verification"


def test_enabled_translation_field_fails():
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    tampered = replace(
        result.record,
        translation_execution_enabled=True,
    )
    kwargs = _verification_args(tampered, req, plan)
    vr = verify_consumption_record(tampered, **kwargs)
    assert vr.valid is False, "Enabled translation field should fail verification"


def test_output_write_enabled_fails():
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    tampered = replace(
        result.record,
        output_write_enabled=True,
    )
    kwargs = _verification_args(tampered, req, plan)
    vr = verify_consumption_record(tampered, **kwargs)
    assert vr.valid is False, "Enabled output write should fail verification"


def test_resume_write_enabled_fails():
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    tampered = replace(
        result.record,
        resume_write_enabled=True,
    )
    kwargs = _verification_args(tampered, req, plan)
    vr = verify_consumption_record(tampered, **kwargs)
    assert vr.valid is False, "Enabled resume write should fail verification"


def test_cache_write_enabled_fails():
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    tampered = replace(
        result.record,
        cache_write_enabled=True,
    )
    kwargs = _verification_args(tampered, req, plan)
    vr = verify_consumption_record(tampered, **kwargs)
    assert vr.valid is False, "Enabled cache write should fail verification"


def test_retry_enabled_fails():
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    tampered = replace(result.record, retry_enabled=True)
    kwargs = _verification_args(tampered, req, plan)
    vr = verify_consumption_record(tampered, **kwargs)
    assert vr.valid is False, "Enabled retry should fail verification"


def test_fallback_enabled_fails():
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    tampered = replace(result.record, fallback_enabled=True)
    kwargs = _verification_args(tampered, req, plan)
    vr = verify_consumption_record(tampered, **kwargs)
    assert vr.valid is False, "Enabled fallback should fail verification"


def test_production_hook_enabled_fails():
    plan, auth_req, auth_dec, freeze_meta, consumer = _make_setup()
    req = _make_valid_consumption_request(
        auth_req.request_fingerprint,
        auth_dec.decision_fingerprint,
        plan.execution_plan_fingerprint,
    )
    result = consumer.prepare_consumption(
        request=req,
        authorization_request=auth_req,
        authorization_decision=auth_dec,
        execution_plan=plan,
        freeze_metadata=freeze_meta,
    )
    tampered = replace(result.record, production_hook_enabled=True)
    kwargs = _verification_args(tampered, req, plan)
    vr = verify_consumption_record(tampered, **kwargs)
    assert vr.valid is False, "Enabled production hook should fail verification"
