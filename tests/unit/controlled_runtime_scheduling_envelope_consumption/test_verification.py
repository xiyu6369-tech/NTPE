from dataclasses import replace

import pytest

from core.controlled_runtime_scheduling_envelope_consumption import (
    ControlledRuntimeSchedulingEnvelopeConsumer,
    SchedulingEnvelopeConsumptionVerificationError,
    verify_controlled_runtime_scheduling_envelope_consumption,
)
from tests.unit.controlled_runtime_scheduling_envelope_consumption import (
    build_context,
)


def _verification(context, claim, **overrides):
    values = {
        key: context[key]
        for key in (
            "request",
            "scheduling_envelope",
            "scheduling_envelope_request",
            "stage67_scheduling_consumption_request",
            "stage67_scheduling_consumption_claim",
            "stage66_scheduling_decision",
            "stage65_handoff_receipt",
            "stage64_envelope",
            "stage63_claim",
            "stage62_record",
            "authorization_decision",
            "execution_plan",
        )
    }
    values.update(
        persisted_payload_json=claim.to_json(),
        persistence_committed=True,
    )
    values.update(overrides)
    return verify_controlled_runtime_scheduling_envelope_consumption(
        claim, **values
    )


def test_authentic_complete_chain_verifies(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeSchedulingEnvelopeConsumer().consume(**context)
    assert result.claim is not None
    verification = _verification(context, result.claim)
    assert verification.valid
    assert verification.reason_codes == ()


@pytest.mark.parametrize(
    "override,reason",
    [
        ({"persistence_committed": False}, "PERSISTENCE_NOT_PROVEN"),
        ({"persisted_payload_json": "{}"}, "CANONICAL_PAYLOAD_MISMATCH"),
    ],
)
def test_persistence_evidence_fails_closed(tmp_path, override, reason):
    context = build_context(tmp_path)
    result = ControlledRuntimeSchedulingEnvelopeConsumer().consume(**context)
    verification = _verification(context, result.claim, **override)
    assert not verification.valid
    assert reason in verification.reason_codes


def test_raise_on_error_uses_stage69_exception(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeSchedulingEnvelopeConsumer().consume(**context)
    with pytest.raises(SchedulingEnvelopeConsumptionVerificationError):
        _verification(
            context,
            result.claim,
            persisted_payload_json="{}",
            raise_on_error=True,
        )


@pytest.mark.parametrize(
    "field",
    [
        "scheduling_envelope_id",
        "scheduling_envelope_fingerprint",
        "scheduling_envelope_request_fingerprint",
        "stage67_claim_fingerprint",
        "stage66_decision_fingerprint",
        "runtime_boundary_id",
    ],
)
def test_request_binding_tampering_is_rejected(tmp_path, field):
    context = build_context(tmp_path)
    request = context["request"]
    value = getattr(request, field)
    replacement = ("0" * 64) if len(value) == 64 else f"{value}-tampered"
    object.__setattr__(request, field, replacement)
    result = ControlledRuntimeSchedulingEnvelopeConsumer().consume(**context)
    assert result.status == "upstream_contract_mismatch"
    assert result.claim is None


@pytest.mark.parametrize("mutation", ["missing", "extra", "reordered", "duplicate"])
def test_malformed_request_chain_is_rejected(tmp_path, mutation):
    context = build_context(tmp_path)
    chain = list(context["request"].upstream_fingerprint_chain)
    if mutation == "missing":
        chain.pop()
    elif mutation == "extra":
        chain.append(chain[-1])
    elif mutation == "reordered":
        chain[0], chain[1] = chain[1], chain[0]
    else:
        chain[1] = chain[0]
    if len(chain) != 23:
        with pytest.raises(ValueError):
            replace(
                context["request"],
                upstream_fingerprint_chain=tuple(chain),
            )
    else:
        context["request"] = replace(
            context["request"], upstream_fingerprint_chain=tuple(chain)
        )
        result = ControlledRuntimeSchedulingEnvelopeConsumer().consume(**context)
        assert result.status == "upstream_contract_mismatch"


