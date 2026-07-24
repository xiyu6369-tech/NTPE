from dataclasses import FrozenInstanceError, replace

import pytest

from core.controlled_runtime_queue_admission_authorization import (
    ControlledRuntimeQueueAdmissionAuthorizer,
    QueueAdmissionAuthorizationVerificationError,
    verify_controlled_runtime_queue_admission_authorization,
)
from core.controlled_runtime_queue_admission_authorization.policy import (
    ADMISSION_INTENT, AUTHORIZED_STATUS,
)
from tests.unit.controlled_runtime_queue_admission_authorization import build_context


def test_authentic_authority_produces_one_immutable_decision(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeQueueAdmissionAuthorizer().authorize(**context)
    decision = result.decision
    assert result.authorized and result.request_count == result.decision_count == 1
    assert decision is not None and len(decision.canonical_chain) == 27
    assert decision.queue_admission_authorized
    assert not any((
        decision.queue_admission_authorization_consumed,
        decision.queue_admission_record_prepared,
        decision.queue_admission_record_consumed,
        decision.queue_record_created,
        decision.runtime_execution_scheduled,
        decision.execution_started,
    ))
    with pytest.raises(FrozenInstanceError):
        decision.queue_admission_authorized = False


def test_repeated_authorization_is_deterministic_and_stateless(tmp_path):
    left_root, right_root = tmp_path / "left", tmp_path / "right"
    left_root.mkdir(); right_root.mkdir()
    left = ControlledRuntimeQueueAdmissionAuthorizer().authorize(**build_context(left_root))
    right = ControlledRuntimeQueueAdmissionAuthorizer().authorize(**build_context(right_root))
    assert left == right


@pytest.mark.parametrize("scope", [True, False, 0, -1, 2, 1.0, "1"])
def test_unit_scope_is_strict_one(tmp_path, scope):
    with pytest.raises((TypeError, ValueError)):
        build_context(tmp_path, unit_scope=scope)


def test_exact_intent_only(tmp_path):
    assert build_context(tmp_path)["request"].admission_intent == ADMISSION_INTENT
    other = tmp_path / "other"
    other.mkdir()
    with pytest.raises(ValueError):
        build_context(other, admission_intent="enqueue")


@pytest.mark.parametrize(
    "field",
    [
        "stage69_claim_fingerprint", "stage69_request_fingerprint",
        "scheduling_envelope_fingerprint", "stage67_claim_fingerprint",
        "stage66_decision_fingerprint", "runtime_boundary_id",
        "selected_adapter_index", "capability_state_fingerprint",
    ],
)
def test_binding_tamper_is_denied(tmp_path, field):
    context = build_context(tmp_path)
    request = context["request"]
    value = getattr(request, field)
    object.__setattr__(
        request, field,
        value + 1 if isinstance(value, int) else (
            "0" * 64 if len(value) == 64 else value + "-tamper"
        ),
    )
    result = ControlledRuntimeQueueAdmissionAuthorizer().authorize(**context)
    assert not result.authorized and result.decision is None


@pytest.mark.parametrize("kind", ["missing", "extra", "duplicate", "reordered"])
def test_chain_tamper_is_rejected(tmp_path, kind):
    context = build_context(tmp_path)
    chain = list(context["request"].upstream_chain)
    if kind == "missing": chain.pop()
    elif kind == "extra": chain.append(chain[-1])
    elif kind == "duplicate": chain[1] = chain[0]
    else: chain[0], chain[1] = chain[1], chain[0]
    if len(chain) != 25:
        with pytest.raises(ValueError):
            replace(context["request"], upstream_chain=tuple(chain))
    else:
        context["request"] = replace(context["request"], upstream_chain=tuple(chain))
        assert not ControlledRuntimeQueueAdmissionAuthorizer().authorize(**context).authorized


@pytest.mark.parametrize(
    "field,value",
    [
        ("persistence_committed", False),
        ("durable_readback_verified", False),
        ("replay_detected", True),
        ("exactly_one_envelope_consumed", False),
    ],
)
def test_invalid_stage69_result_evidence_is_denied(tmp_path, field, value):
    context = build_context(tmp_path)
    context["stage69_result"] = replace(context["stage69_result"], **{field: value})
    result = ControlledRuntimeQueueAdmissionAuthorizer().authorize(**context)
    assert not result.authorized


def test_verifier_raise_on_error(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeQueueAdmissionAuthorizer().authorize(**context)
    bad = replace(result.decision, queue_record_created=False)
    object.__setattr__(bad, "decision_fingerprint", "0" * 64)
    with pytest.raises(QueueAdmissionAuthorizationVerificationError):
        verify_controlled_runtime_queue_admission_authorization(
            bad, request=context["request"],
            stage69_claim=context["stage69_claim"],
            stage69_request=context["stage69_request"],
            stage69_result=context["stage69_result"],
            stage69_verification_context=context["stage69_verification_context"],
            raise_on_error=True,
        )

