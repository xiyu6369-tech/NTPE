from dataclasses import FrozenInstanceError

import pytest

from core.controlled_runtime_scheduling_envelope import (
    ControlledRuntimeSchedulingEnvelopeBuilder,
    ControlledRuntimeSchedulingEnvelopePolicy,
)
from core.controlled_runtime_scheduling_envelope.policy import (
    DEFAULT_POLICY,
    exact_scheduling_scope,
)
from . import build_context


def test_policy_is_exact_and_immutable():
    assert DEFAULT_POLICY.complete_chain_layers == 23
    assert DEFAULT_POLICY.schedule_unit_count == 1
    assert DEFAULT_POLICY.maximum_provider_requests == 1
    assert DEFAULT_POLICY.maximum_translation_requests == 1
    assert DEFAULT_POLICY.maximum_retries == 0
    assert DEFAULT_POLICY.maximum_fallbacks == 0
    with pytest.raises(FrozenInstanceError):
        DEFAULT_POLICY.complete_chain_layers = 24


def test_exact_scope_binds_stage67_and_runtime_boundary(tmp_path):
    request = build_context(tmp_path)["request"]
    assert request.stage67_scheduling_consumption_claim_fingerprint in (
        request.scheduling_scope
    )
    assert '"runtime_boundary_kind":"controlled_offline_acceptance_boundary"' in (
        request.scheduling_scope
    )


def test_scope_is_mapping_order_stable(tmp_path):
    request = build_context(tmp_path)["request"]
    values = {
        name: getattr(request, name)
        for name in (
            "scheduling_consumption_id",
            "scheduling_authorization_id",
            "handoff_id",
            "envelope_id",
            "claim_id",
            "consumption_id",
            "authorization_id",
            "execution_plan_fingerprint",
            "execution_authorization_decision_fingerprint",
            "stage63_claim_fingerprint",
            "stage64_envelope_fingerprint",
            "stage65_handoff_receipt_fingerprint",
            "stage66_scheduling_request_fingerprint",
            "stage66_scheduling_decision_fingerprint",
            "stage67_scheduling_consumption_request_fingerprint",
            "stage67_scheduling_consumption_claim_fingerprint",
            "selected_adapter_index",
            "runtime_boundary_id",
            "runtime_boundary_kind",
        )
    }
    assert exact_scheduling_scope(**dict(reversed(tuple(values.items())))) == (
        request.scheduling_scope
    )


def test_builder_rejects_policy_substitution():
    with pytest.raises(ValueError):
        ControlledRuntimeSchedulingEnvelopeBuilder(
            policy=ControlledRuntimeSchedulingEnvelopePolicy(
                complete_chain_layers=24
            )
        )
