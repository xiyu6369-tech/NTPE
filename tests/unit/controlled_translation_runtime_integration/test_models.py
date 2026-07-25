from dataclasses import FrozenInstanceError, fields

import pytest

from core.controlled_translation_runtime_integration import (
    ControlledTranslationExecutionRequest, ControlledTranslationExecutor,
    ControlledTranslationOutputEvidence, ControlledTranslationVerificationResult,
)
from core.controlled_translation_runtime_integration.policy import (
    EVIDENCE_SCHEMA_NAME, REQUEST_SCHEMA_NAME, RESULT_SCHEMA_NAME,
    VERIFICATION_SCHEMA_NAME,
)
from tests.unit.controlled_translation_runtime_integration import build_context


def test_request_is_immutable_deterministic_and_versioned(tmp_path):
    context = build_context(tmp_path)
    request = context["request"]
    clone = ControlledTranslationExecutionRequest(
        **{item.name: getattr(request, item.name) for item in fields(request) if item.init}
    )
    assert clone == request and request.schema_name == REQUEST_SCHEMA_NAME
    with pytest.raises(FrozenInstanceError):
        request.unit_scope = 2


@pytest.mark.parametrize("scope,error", [(True, TypeError), (1.0, TypeError), (0, ValueError), (2, ValueError)])
def test_scope_is_strict(tmp_path, scope, error):
    with pytest.raises(error):
        build_context(tmp_path, unit_scope=scope)


@pytest.mark.parametrize("field,value", [
    ("target_language", "zh-CN"), ("translation_profile", "general"),
])
def test_language_and_profile_fail_closed(tmp_path, field, value):
    with pytest.raises(ValueError):
        build_context(tmp_path, **{field: value})


def test_success_result_and_evidence_are_immutable(tmp_path):
    result, evidence = ControlledTranslationExecutor().execute(**build_context(tmp_path))
    assert result.schema_name == RESULT_SCHEMA_NAME
    assert evidence.schema_name == EVIDENCE_SCHEMA_NAME
    assert isinstance(evidence, ControlledTranslationOutputEvidence)
    assert len(evidence.canonical_chain) == 41
    with pytest.raises(FrozenInstanceError):
        evidence.quality_passed = False


def test_verification_result_is_immutable():
    value = ControlledTranslationVerificationResult(
        valid=False, schema_verified=False, identity_verified=False,
        binding_verified=False, chain_verified=False, scope_verified=False,
        provider_counts_verified=False, output_verified=False,
        quality_verified=False, state_verified=False,
        prohibited_counters_verified=False, reason_codes=("INVALID_SCHEMA",),
    )
    assert value.schema_name == VERIFICATION_SCHEMA_NAME
    with pytest.raises(FrozenInstanceError):
        value.valid = True
