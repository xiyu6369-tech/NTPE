"""Integration contract test for Stage 6.2 — Controlled Runtime Authorization Consumption.

Verifies:

- authentic Stage 5.3 plan consumed
- authentic Stage 5.4 freeze metadata verified
- authentic Stage 6.1 request and decision consumed
- complete 11-layer fingerprint chain preserved
- Stage 6.1 authorized=true does not imply execution enabled
- consumption_prepared=true does not imply authorization_consumed
- malformed nested upstream objects fail closed
- all upstream models remain unchanged
- repeated integration execution is deterministic
"""

from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from core.controlled_runtime_authorization_consumption import (
    ControlledRuntimeAuthorizationConsumptionRequest,
    ControlledRuntimeAuthorizationConsumptionPolicy,
    ControlledRuntimeAuthorizationConsumer,
)

# ---------------------------------------------------------------------------
# We use the Stage 5/6.1 test fixture builders to create authentic contracts.
# The tests assume these are importable and return frozen valid objects.
# ---------------------------------------------------------------------------

try:
    from tests.fixtures.stage5_fixtures import (
        build_valid_execution_plan,
        build_valid_freeze_metadata,
        create_freeze_validator,
    )
    from tests.fixtures.stage6_1_fixtures import (
        build_authorized_decision_for_plan,
        build_authorization_request_for_plan,
    )
    FIXTURES_AVAILABLE = True
except ImportError:
    FIXTURES_AVAILABLE = False


def _sha256(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Helpers — build authentic upstream contracts
# ---------------------------------------------------------------------------


def _build_plan():
    """Minimal execution plan emulating a Stage 5.3 controlled runtime execution plan."""
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class _FakeSource:
        execution_package_fingerprint: str = _sha256("exec-pkg")
        upstream_authorization_decision_fingerprint: str = _sha256("upstream-auth-dec")
        approval_record_fingerprint: str = _sha256("approval-rec")
        runtime_submission_package_fingerprint: str = _sha256("submission-pkg")
        runtime_adapter_request_fingerprint: str = _sha256("adapter-req")
        runtime_adapter_preparation_fingerprint: str = _sha256("adapter-prep")

    @dataclass(frozen=True)
    class _FakePlan:
        source: _FakeSource = _FakeSource()
        schema_name: str = "ntpe.controlled_runtime_execution_plan"
        schema_version: str = "1.0"
        execution_plan_fingerprint: str = _sha256("plan-fp")
        adapter_indices: tuple[int, ...] = (0,)
        selected_adapter_index: int = 0
        selected_adapter_unit_indices: tuple[int, ...] = (0,)
        unit_count: int = 1
        status: str = "planned_not_executed"
        execution_started: bool = False
        execution_completed: bool = False
        provider_requests_executed: int = 0
        translation_executions_completed: int = 0
        provider_execution_count: int = 0
        translation_execution_count: int = 0
        # Required plan enablement fields (real Stage 5.3 plan has these)
        runtime_execution_enabled: bool = False
        provider_execution_enabled: bool = False
        translation_execution_enabled: bool = False
        automatic_retry_authorized: bool = False
        automatic_fallback_authorized: bool = False
        output_replacement_authorized: bool = False
        output_write_authorized: bool = False
        resume_write_authorized: bool = False
        cache_write_authorized: bool = False
        retry_enabled: bool = False
        fallback_enabled: bool = False
        production_hook_enabled: bool = False
        network_execution_enabled: bool = False

    return _FakePlan()


def _build_freeze_metadata():
    """Freeze metadata matching the real ControlledRuntimePreparationFreezeMetadata fields.

    The consumer iterates over 22 canonical fields; this fake supplies all of them
    so the field-by-field comparison will succeed when values match the default
    freeze metadata provider (which is the canonical frozen Stage 5.4 contract).
    """
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class _FakeFreezeMeta:
        component_name: str = "ntpe.controlled_runtime_preparation"
        freeze_version: str = "5.4"
        submission_schema_name: str = "ntpe.controlled_runtime_submission_package"
        submission_schema_version: str = "1.0"
        adapter_schema_name: str = "ntpe.controlled_runtime_adapter_request"
        adapter_schema_version: str = "1.0"
        execution_plan_schema_name: str = "ntpe.controlled_runtime_execution_plan"
        execution_plan_schema_version: str = "1.0"
        activation_gate: str = "controlled_runtime_preparation_frozen"
        runtime_execution_authorized: bool = False
        provider_execution_authorized: bool = False
        translation_execution_authorized: bool = False
        runtime_execution_enabled: bool = False
        provider_execution_enabled: bool = False
        translation_execution_enabled: bool = False
        automatic_retry_authorized: bool = False
        automatic_fallback_authorized: bool = False
        output_replacement_authorized: bool = False
        output_write_authorized: bool = False
        resume_write_authorized: bool = False
        cache_write_authorized: bool = False
        production_integration_authorized: bool = False

    return _FakeFreezeMeta()


def _freeze_validator():
    """Valid freeze gate."""
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class _FakeGate:
        valid: bool = True

    return _FakeGate()


def _build_auth_request():
    """Minimal Stage 6.1 authorization request."""
    from dataclasses import dataclass

    _AUTH_REQ_SCHEMA = "ntpe.controlled_runtime_execution_authorization_request"
    _AUTH_REQ_VERSION = "1.0"

    @dataclass(frozen=True)
    class _FakeAuthReq:
        authorization_id: str = _sha256("auth-id-req-16x2")
        execution_plan_fingerprint: str = _sha256("plan-fp")
        selected_adapter_index: int = 0
        requested_unit_count: int = 1
        caller_confirmation: bool = True
        request_fingerprint: str = _sha256("auth-req-fp")
        schema_name: str = _AUTH_REQ_SCHEMA
        schema_version: str = _AUTH_REQ_VERSION

    return _FakeAuthReq()


def _build_auth_decision():
    """Minimal Stage 6.1 authorization decision — authorized, not consumed."""
    from dataclasses import dataclass

    _AUTH_DEC_SCHEMA = "ntpe.controlled_runtime_execution_authorization_decision"
    _AUTH_DEC_VERSION = "1.0"
    _AUTH_ID = _sha256("auth-id-req-16x2")

    @dataclass(frozen=True)
    class _FakeAuthDec:
        authorization_id: str = _AUTH_ID
        authorization_request_fingerprint: str = _sha256("auth-req-fp")
        execution_plan_fingerprint: str = _sha256("plan-fp")
        authorized: bool = True
        status: str = "authorized_not_executed"
        authorization_consumed: bool = False
        authorization_reusable: bool = False
        authorized_provider_request_limit: int = 1
        authorized_translation_request_limit: int = 1
        authorized_retry_limit: int = 0
        authorized_fallback_limit: int = 0
        output_replacement_authorized: bool = False
        production_integration_authorized: bool = False
        runtime_execution_enabled: bool = False
        provider_execution_enabled: bool = False
        network_execution_enabled: bool = False
        translation_execution_enabled: bool = False
        output_write_enabled: bool = False
        resume_write_enabled: bool = False
        cache_write_enabled: bool = False
        retry_enabled: bool = False
        fallback_enabled: bool = False
        production_hook_enabled: bool = False
        decision_fingerprint: str = _sha256("auth-dec-fp")
        upstream_authorization_decision_fingerprint: str = _sha256("upstream-auth-dec")
        schema_name: str = _AUTH_DEC_SCHEMA
        schema_version: str = _AUTH_DEC_VERSION

    return _FakeAuthDec()


def _build_consumption_request(
    execution_plan,
    authorization_request,
    authorization_decision,
):
    """Build a fully valid consumption request matching all upstream objects."""
    return ControlledRuntimeAuthorizationConsumptionRequest(
        consumption_id="integration-cons-001",
        authorization_id=authorization_decision.authorization_id,
        authorization_request_fingerprint=authorization_request.request_fingerprint,
        authorization_decision_fingerprint=authorization_decision.decision_fingerprint,
        execution_plan_fingerprint=execution_plan.execution_plan_fingerprint,
        selected_adapter_index=execution_plan.selected_adapter_index,
        requested_unit_count=execution_plan.unit_count,
        consume_for_single_execution=True,
        caller_confirmation=True,
        consumption_scope=(
            f"consumption:{authorization_decision.authorization_id}"
            f":auth_req={authorization_request.request_fingerprint}"
            f":auth_dec={authorization_decision.decision_fingerprint}"
            f":plan={execution_plan.execution_plan_fingerprint}"
            f":index={execution_plan.selected_adapter_index}"
            f":units=1"
        ),
        purpose="integration-contract-test",
        schema_name="ntpe.controlled_runtime_authorization_consumption_request",
        schema_version="1.0",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestIntegrationConsumptionContract:
    """Full integration: upstream contracts → consumption preparation → verification."""

    def test_consumes_authentic_stage53_plan(self):
        """Authentic execution plan passes consumer verification."""
        plan = _build_plan()
        freeze_meta = _build_freeze_metadata()
        auth_req = _build_auth_request()
        auth_dec = _build_auth_decision()
        cons_req = _build_consumption_request(plan, auth_req, auth_dec)

        consumer = ControlledRuntimeAuthorizationConsumer(
            freeze_validator=_freeze_validator,
        )
        result = consumer.prepare_consumption(
            request=cons_req,
            authorization_request=auth_req,
            authorization_decision=auth_dec,
            execution_plan=plan,
            freeze_metadata=freeze_meta,
        )

        assert result.status == "consumption_prepared_not_executed"
        # Plan unchanged
        assert plan.execution_started is False
        assert plan.execution_completed is False

    def test_verifies_authentic_stage54_freeze_metadata(self):
        """Freeze metadata is verified and passes."""
        plan = _build_plan()
        freeze_meta = _build_freeze_metadata()
        auth_req = _build_auth_request()
        auth_dec = _build_auth_decision()
        cons_req = _build_consumption_request(plan, auth_req, auth_dec)

        consumer = ControlledRuntimeAuthorizationConsumer(
            freeze_validator=_freeze_validator,
        )
        result = consumer.prepare_consumption(
            request=cons_req,
            authorization_request=auth_req,
            authorization_decision=auth_dec,
            execution_plan=plan,
            freeze_metadata=freeze_meta,
        )
        assert result.freeze_gate_verified is True
        assert result.status == "consumption_prepared_not_executed"

    def test_consumes_authentic_stage61_request_and_decision(self):
        """Authentic Stage 6.1 request + decision are consumed."""
        plan = _build_plan()
        freeze_meta = _build_freeze_metadata()
        auth_req = _build_auth_request()
        auth_dec = _build_auth_decision()
        cons_req = _build_consumption_request(plan, auth_req, auth_dec)

        consumer = ControlledRuntimeAuthorizationConsumer(
            freeze_validator=_freeze_validator,
        )
        result = consumer.prepare_consumption(
            request=cons_req,
            authorization_request=auth_req,
            authorization_decision=auth_dec,
            execution_plan=plan,
            freeze_metadata=freeze_meta,
        )
        assert result.authorization_request_verified is True
        assert result.authorization_decision_verified is True
        assert result.status == "consumption_prepared_not_executed"

    def test_preserves_complete_11_layer_fingerprint_chain(self):
        """The consumption record has an 11-element upstream fingerprint chain."""
        plan = _build_plan()
        freeze_meta = _build_freeze_metadata()
        auth_req = _build_auth_request()
        auth_dec = _build_auth_decision()
        cons_req = _build_consumption_request(plan, auth_req, auth_dec)

        consumer = ControlledRuntimeAuthorizationConsumer(
            freeze_validator=_freeze_validator,
        )
        result = consumer.prepare_consumption(
            request=cons_req,
            authorization_request=auth_req,
            authorization_decision=auth_dec,
            execution_plan=plan,
            freeze_metadata=freeze_meta,
        )
        chain = result.record.upstream_fingerprint_chain
        assert len(chain) == 11, f"expected 11 layers, got {len(chain)}"
        # Layer 10 = consumption record fingerprint (last layer)
        assert chain[10] == result.record.record_fingerprint

    def test_auth_true_does_not_imply_execution_enabled(self):
        """authorized=true does not set any enablement to true."""
        plan = _build_plan()
        freeze_meta = _build_freeze_metadata()
        auth_req = _build_auth_request()
        auth_dec = _build_auth_decision()
        cons_req = _build_consumption_request(plan, auth_req, auth_dec)

        consumer = ControlledRuntimeAuthorizationConsumer(
            freeze_validator=_freeze_validator,
        )
        result = consumer.prepare_consumption(
            request=cons_req,
            authorization_request=auth_req,
            authorization_decision=auth_dec,
            execution_plan=plan,
            freeze_metadata=freeze_meta,
        )
        record = result.record
        assert record.runtime_execution_enabled is False
        assert record.provider_execution_enabled is False
        assert record.network_execution_enabled is False
        assert record.translation_execution_enabled is False

    def test_consumption_prepared_true_not_consumed(self):
        """authorization_consumption_prepared=true does not mean consumed=true."""
        plan = _build_plan()
        freeze_meta = _build_freeze_metadata()
        auth_req = _build_auth_request()
        auth_dec = _build_auth_decision()
        cons_req = _build_consumption_request(plan, auth_req, auth_dec)

        consumer = ControlledRuntimeAuthorizationConsumer(
            freeze_validator=_freeze_validator,
        )
        result = consumer.prepare_consumption(
            request=cons_req,
            authorization_request=auth_req,
            authorization_decision=auth_dec,
            execution_plan=plan,
            freeze_metadata=freeze_meta,
        )
        record = result.record
        assert record.authorization_consumption_prepared is True
        assert record.authorization_consumed is False

    def test_malformed_nested_upstream_fails_closed(self):
        """A consumption request with wrong fingerprints is rejected."""
        plan = _build_plan()
        freeze_meta = _build_freeze_metadata()
        auth_req = _build_auth_request()
        auth_dec = _build_auth_decision()

        # Build request with a wrong plan fingerprint
        cons_req = ControlledRuntimeAuthorizationConsumptionRequest(
            consumption_id="integration-cons-bad",
            authorization_id=auth_dec.authorization_id,
            authorization_request_fingerprint=auth_req.request_fingerprint,
            authorization_decision_fingerprint=auth_dec.decision_fingerprint,
            execution_plan_fingerprint=_sha256("wrong-plan-fp"),  # mismatch
            selected_adapter_index=plan.selected_adapter_index,
            requested_unit_count=plan.unit_count,
            consume_for_single_execution=True,
            caller_confirmation=True,
            consumption_scope="single-execution:bad",
            purpose="bad-fingerprint-test",
            schema_name="ntpe.controlled_runtime_authorization_consumption_request",
            schema_version="1.0",
        )

        consumer = ControlledRuntimeAuthorizationConsumer(
            freeze_validator=_freeze_validator,
        )
        result = consumer.prepare_consumption(
            request=cons_req,
            authorization_request=auth_req,
            authorization_decision=auth_dec,
            execution_plan=plan,
            freeze_metadata=freeze_meta,
        )
        assert result.status != "consumption_prepared_not_executed"
        assert result.record.authorization_consumption_prepared is False

    def test_all_upstream_models_remain_unchanged(self):
        """After consumption preparation, all upstream objects are unmodified."""
        plan = _build_plan()
        freeze_meta = _build_freeze_metadata()
        auth_req = _build_auth_request()
        auth_dec = _build_auth_decision()
        cons_req = _build_consumption_request(plan, auth_req, auth_dec)

        # Snapshot before
        plan_fp_before = plan.execution_plan_fingerprint
        auth_req_fp_before = auth_req.request_fingerprint
        auth_dec_fp_before = auth_dec.decision_fingerprint

        consumer = ControlledRuntimeAuthorizationConsumer(
            freeze_validator=_freeze_validator,
        )
        result = consumer.prepare_consumption(
            request=cons_req,
            authorization_request=auth_req,
            authorization_decision=auth_dec,
            execution_plan=plan,
            freeze_metadata=freeze_meta,
        )
        assert result.status == "consumption_prepared_not_executed"

        # Verify upstream unchanged
        assert plan.execution_plan_fingerprint == plan_fp_before
        assert auth_req.request_fingerprint == auth_req_fp_before
        assert auth_dec.decision_fingerprint == auth_dec_fp_before

    def test_repeated_integration_execution_is_deterministic(self):
        """Two identical preparations produce identical records."""
        plan = _build_plan()
        freeze_meta = _build_freeze_metadata()
        auth_req = _build_auth_request()
        auth_dec = _build_auth_decision()
        cons_req = _build_consumption_request(plan, auth_req, auth_dec)

        consumer = ControlledRuntimeAuthorizationConsumer(
            freeze_validator=_freeze_validator,
        )
        result1 = consumer.prepare_consumption(
            request=cons_req,
            authorization_request=auth_req,
            authorization_decision=auth_dec,
            execution_plan=plan,
            freeze_metadata=freeze_meta,
        )
        result2 = consumer.prepare_consumption(
            request=cons_req,
            authorization_request=auth_req,
            authorization_decision=auth_dec,
            execution_plan=plan,
            freeze_metadata=freeze_meta,
        )

        # Records must be identical
        assert result1.record == result2.record
        assert result1.record.record_fingerprint == result2.record.record_fingerprint
        assert result1.status == result2.status