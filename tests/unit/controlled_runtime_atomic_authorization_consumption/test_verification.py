from dataclasses import replace

import pytest

from core.controlled_runtime_atomic_authorization_consumption import (
    AtomicAuthorizationConsumer,
    verify_atomic_consumption_claim,
)
from . import build_context


def test_committed_claim_verifies_and_tampering_fails(tmp_path):
    context = build_context(tmp_path)
    result = AtomicAuthorizationConsumer().consume(**context)
    verification = verify_atomic_consumption_claim(
        result.claim, request=context["request"],
        stage62_request=context["stage62_request"], stage62_record=context["stage62_record"],
        authorization_request=context["authorization_request"],
        authorization_decision=context["authorization_decision"],
        execution_plan=context["execution_plan"],
    )
    assert verification.valid
    tampered = replace(result.claim, runtime_execution_enabled=True)
    assert not verify_atomic_consumption_claim(tampered, request=context["request"]).valid


@pytest.mark.parametrize("field,value", (
    ("authorization_reusable", True),
    ("durable_reuse_prevention_established", False),
    ("persistent_registry_written", False),
    ("execution_started", True), ("execution_completed", True),
    ("runtime_execution_enabled", True), ("provider_execution_enabled", True),
    ("network_execution_enabled", True), ("translation_execution_enabled", True),
    ("output_write_enabled", True), ("resume_write_enabled", True),
    ("cache_write_enabled", True), ("retry_enabled", True),
    ("fallback_enabled", True), ("production_hook_enabled", True),
))
def test_every_forbidden_claim_capability_or_state_fails(tmp_path, field, value):
    context = build_context(tmp_path)
    claim = AtomicAuthorizationConsumer().consume(**context).claim
    assert not verify_atomic_consumption_claim(replace(claim, **{field: value}), request=context["request"]).valid
