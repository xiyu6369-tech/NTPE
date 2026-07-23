"""Stage 6.2 unit tests — models and exports."""

from __future__ import annotations

import pytest

from core.controlled_runtime_authorization_consumption import (
    ControlledRuntimeAuthorizationConsumptionRequest,
    ControlledRuntimeAuthorizationConsumptionRecord,
    ControlledRuntimeAuthorizationConsumptionResult,
    ControlledRuntimeAuthorizationConsumptionFinding,
)

import core.controlled_runtime_authorization_consumption as pkg


# ---------------------------------------------------------------------------
# 1. consumption request is immutable
# ---------------------------------------------------------------------------


def test_request_immutable() -> None:
    req = ControlledRuntimeAuthorizationConsumptionRequest(
        consumption_id="consume-001",
        authorization_id="auth-001",
        authorization_request_fingerprint="a" * 64,
        authorization_decision_fingerprint="b" * 64,
        execution_plan_fingerprint="c" * 64,
        selected_adapter_index=0,
        requested_unit_count=1,
        consume_for_single_execution=True,
        caller_confirmation=True,
        consumption_scope="test-scope",
        purpose="test",
        schema_name="ntpe.controlled_runtime_authorization_consumption_request",
        schema_version="1.0",
    )
    with pytest.raises(Exception):
        req.consumption_id = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 2. consumption record is immutable
# ---------------------------------------------------------------------------


def test_record_immutable() -> None:
    rec = ControlledRuntimeAuthorizationConsumptionRecord(
        consumption_id="consume-001",
        authorization_id="auth-001",
        authorization_request_fingerprint="a" * 64,
        authorization_decision_fingerprint="b" * 64,
        execution_plan_fingerprint="c" * 64,
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
        reason_codes=(),
        upstream_fingerprint_chain=tuple("f" * 64 for _ in range(11)),
        consumption_request_fingerprint="r" * 64,
        schema_name="ntpe.controlled_runtime_authorization_consumption_record",
        schema_version="1.0",
    )
    with pytest.raises(Exception):
        rec.authorization_consumed = True  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 3. consumption result is immutable
# ---------------------------------------------------------------------------


def test_result_immutable() -> None:
    req = ControlledRuntimeAuthorizationConsumptionRequest(
        consumption_id="consume-001",
        authorization_id="auth-001",
        authorization_request_fingerprint="a" * 64,
        authorization_decision_fingerprint="b" * 64,
        execution_plan_fingerprint="c" * 64,
        selected_adapter_index=0,
        requested_unit_count=1,
        consume_for_single_execution=True,
        caller_confirmation=True,
        consumption_scope="test-scope",
        purpose="test",
        schema_name="ntpe.controlled_runtime_authorization_consumption_request",
        schema_version="1.0",
    )
    rec = ControlledRuntimeAuthorizationConsumptionRecord(
        consumption_id="consume-001",
        authorization_id="auth-001",
        authorization_request_fingerprint="a" * 64,
        authorization_decision_fingerprint="b" * 64,
        execution_plan_fingerprint="c" * 64,
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
        reason_codes=(),
        upstream_fingerprint_chain=tuple("f" * 64 for _ in range(11)),
        consumption_request_fingerprint="r" * 64,
        schema_name="ntpe.controlled_runtime_authorization_consumption_record",
        schema_version="1.0",
    )
    result = ControlledRuntimeAuthorizationConsumptionResult(
        request=req,
        record=rec,
        freeze_gate_verified=True,
        execution_plan_verified=True,
        authorization_request_verified=True,
        authorization_decision_verified=True,
        authorization_binding_verified=True,
        prior_consumption_state_verified=True,
        policy_findings=(),
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
    with pytest.raises(Exception):
        result.runtime_invoked = True  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 4. nested findings are immutable
# ---------------------------------------------------------------------------


def test_finding_immutable() -> None:
    f = ControlledRuntimeAuthorizationConsumptionFinding(
        code="TEST",
        severity="info",
        message="test message",
        field="test_field",
        expected="exp",
        observed="obs",
    )
    with pytest.raises(Exception):
        f.code = "CHANGED"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 5. tuple collections are immutable
# ---------------------------------------------------------------------------


def test_policy_findings_tuple_immutable() -> None:
    f1 = ControlledRuntimeAuthorizationConsumptionFinding(
        code="TEST1",
        severity="blocking",
        message="m1",
        field="f1",
        expected="e1",
        observed="o1",
    )
    f2 = ControlledRuntimeAuthorizationConsumptionFinding(
        code="TEST2",
        severity="info",
        message="m2",
        field="f2",
        expected="e2",
        observed="o2",
    )
    t = (f1, f2)
    with pytest.raises(Exception):
        t[0] = f2  # type: ignore[index]


# ---------------------------------------------------------------------------
# 6. exact request schema
# ---------------------------------------------------------------------------


def test_request_schema_values() -> None:
    req = ControlledRuntimeAuthorizationConsumptionRequest(
        consumption_id="cid",
        authorization_id="aid",
        authorization_request_fingerprint="a" * 64,
        authorization_decision_fingerprint="b" * 64,
        execution_plan_fingerprint="c" * 64,
        selected_adapter_index=0,
        requested_unit_count=1,
        consume_for_single_execution=True,
        caller_confirmation=True,
        consumption_scope="scope",
        purpose="p",
        schema_name="ntpe.controlled_runtime_authorization_consumption_request",
        schema_version="1.0",
    )
    assert req.schema_name == "ntpe.controlled_runtime_authorization_consumption_request"
    assert req.schema_version == "1.0"


# ---------------------------------------------------------------------------
# 7. exact record schema
# ---------------------------------------------------------------------------


def test_record_schema_values() -> None:
    rec = ControlledRuntimeAuthorizationConsumptionRecord(
        consumption_id="cid",
        authorization_id="aid",
        authorization_request_fingerprint="a" * 64,
        authorization_decision_fingerprint="b" * 64,
        execution_plan_fingerprint="c" * 64,
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
        reason_codes=(),
        upstream_fingerprint_chain=tuple("f" * 64 for _ in range(11)),
        consumption_request_fingerprint="r" * 64,
        schema_name="ntpe.controlled_runtime_authorization_consumption_record",
        schema_version="1.0",
    )
    assert rec.schema_name == "ntpe.controlled_runtime_authorization_consumption_record"
    assert rec.schema_version == "1.0"


# ---------------------------------------------------------------------------
# 8. private helpers are not exported
# ---------------------------------------------------------------------------


def test_private_not_exported() -> None:
    all_symbols = set(pkg.__all__)
    assert "_FindingCollector" not in all_symbols
    assert "_FINDING_CODES" not in all_symbols
    assert "exact_consumption_scope" not in all_symbols
    assert "DEFAULT_POLICY" not in all_symbols


# ---------------------------------------------------------------------------
# 9. public API contains only intended symbols
# ---------------------------------------------------------------------------


def test_public_api_exact() -> None:
    expected = {
        "ControlledRuntimeAuthorizationConsumptionRequest",
        "ControlledRuntimeAuthorizationConsumptionRecord",
        "ControlledRuntimeAuthorizationConsumptionResult",
        "ControlledRuntimeAuthorizationConsumptionPolicy",
        "ControlledRuntimeAuthorizationConsumer",
        "ConsumptionRecordVerificationResult",
        "verify_consumption_record",
    }
    assert set(pkg.__all__) == expected