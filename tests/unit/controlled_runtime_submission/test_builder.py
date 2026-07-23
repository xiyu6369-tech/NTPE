from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pytest

from core.book_preparation import BookPreparationFinding, BookPreparationProcessor
from core.controlled_runtime_submission import (
    ControlledRuntimeSubmissionBuilder,
    InvalidRuntimeSubmissionInputError,
    RuntimeSubmissionConsistencyError,
    RuntimeSubmissionPolicyError,
    RuntimeSubmissionScopeError,
)
from core.translation_execution_approval import (
    ExplicitHumanApprovalRequest,
    TranslationExecutionApprover,
)
from core.translation_execution_authorization import TranslationExecutionAuthorizationEvaluator
from core.translation_execution_package import TranslationExecutionPackageBuilder


def _corrupt(target, **changes):
    candidate = copy.copy(target)
    for name, value in changes.items():
        object.__setattr__(candidate, name, value)
    return candidate


def _chain(tmp_path: Path, approval_type="full_package", indices=None, warning=False):
    text = (
        "Chapter 1\n" + "Sentence. " * 300 + "\nChapter 2\n" + "More sentence. " * 300
        if warning
        else "Chapter 1\n" + "Sentence. " * 180 + "\nChapter 2\n" + "Another sentence. " * 110
    )
    path = tmp_path / "novel.txt"
    path.write_bytes(text.encode("utf-8"))
    preparation = BookPreparationProcessor().prepare(path)
    if warning:
        assert preparation.status == "ready_with_warnings"
    package = TranslationExecutionPackageBuilder().build(preparation)
    decision = TranslationExecutionAuthorizationEvaluator().evaluate(package)
    indices = tuple(range(package.unit_count)) if indices is None else indices
    statement = "APPROVE_CONTROLLED_TRANSLATION_EXECUTION: approved scope"
    if package.status == "prepared_with_warnings":
        statement += " ACKNOWLEDGE_PACKAGE_WARNINGS"
    request = ExplicitHumanApprovalRequest(
        approval_type=approval_type,
        approved_package_fingerprint=package.execution_package_fingerprint,
        approved_authorization_fingerprint=decision.authorization_fingerprint,
        approved_unit_indices=indices,
        approve_provider_execution=True,
        approve_translation_execution=True,
        approve_runtime_submission=True,
        approve_automatic_retry=False,
        approve_automatic_fallback=False,
        approve_output_replacement=False,
        approval_statement=statement,
        approval_reference="stage51-unit-test",
    )
    record = TranslationExecutionApprover().approve(
        package=package, authorization_decision=decision, approval_request=request
    )
    return package, decision, record, text


def _build(chain):
    package, decision, record, _ = chain
    return ControlledRuntimeSubmissionBuilder().build(
        package=package, authorization_decision=decision, approval_record=record
    )


def test_full_package_maps_units_content_offsets_flags_and_coverage(tmp_path: Path) -> None:
    chain = _chain(tmp_path)
    package, _, _, text = chain
    submission = _build(chain)
    assert submission.submission_unit_count == package.unit_count
    assert submission.approved_unit_indices == tuple(range(package.unit_count))
    assert submission.is_full_package_submission is True
    assert submission.reconstruct_approved_text() == text
    assert submission.approval_coverage_ratio == submission.coverage_ratio == 1.0
    assert submission.covered_character_count == submission.character_count
    for submission_index, (mapped, original) in enumerate(zip(submission.units, package.units)):
        assert mapped.submission_index == submission_index
        assert mapped.execution_unit_index == original.index
        assert mapped.execution_unit_id == original.unit_id
        assert mapped.text == original.text
        assert mapped.source_character_start == original.source_character_start
        assert mapped.source_character_end == original.source_character_end
        assert mapped.section_indices == original.section_indices
        assert mapped.heading_text == original.heading_text
        assert mapped.boundary_reason == original.boundary_reason
        assert mapped.source_chunk_fingerprint == original.source_chunk_fingerprint
        assert mapped.execution_unit_fingerprint == original.execution_unit_fingerprint
        assert mapped.status == "queued_for_controlled_submission"
        assert (mapped.runtime_attempt_count, mapped.provider_request_count) == (0, 0)
        assert mapped.translation_result_attached is False
    assert (submission.provider_execution_authorized,
            submission.translation_execution_authorized,
            submission.runtime_submission_authorized) == (True, True, True)
    assert not submission.automatic_retry_authorized
    assert not submission.automatic_fallback_authorized
    assert not submission.output_replacement_authorized
    assert not submission.runtime_submission_executed
    assert submission.provider_requests_executed == submission.translation_executions_completed == 0
    assert {finding.code for finding in submission.findings} >= {
        "CONTROLLED_RUNTIME_SUBMISSION_PREPARED", "FULL_PACKAGE_SUBMISSION",
        "RUNTIME_SUBMISSION_NOT_EXECUTED", "PROVIDER_REQUEST_COUNT_ZERO",
        "TRANSLATION_EXECUTION_COUNT_ZERO",
    }


@pytest.mark.parametrize(("approval_type", "scope"), [("single_unit", (0,)), ("selected_units", (1,))])
def test_partial_scope_is_exact_and_coverage_is_distinct(tmp_path: Path, approval_type, scope) -> None:
    chain = _chain(tmp_path, approval_type, scope)
    package = chain[0]
    if max(scope) >= package.unit_count:
        pytest.skip("fixture produced too few units")
    submission = _build(chain)
    assert tuple(unit.execution_unit_index for unit in submission.units) == scope
    assert submission.reconstruct_approved_text() == "".join(package.units[i].text for i in scope)
    assert submission.is_full_package_submission is False
    assert 0 < submission.approval_coverage_ratio < 1
    assert submission.coverage_ratio == 1.0
    assert "PARTIAL_SCOPE_SUBMISSION" in {finding.code for finding in submission.findings}


def test_warning_status_and_finding_propagate(tmp_path: Path) -> None:
    submission = _build(_chain(tmp_path, warning=True))
    assert submission.status == "prepared_for_controlled_submission_with_warnings"
    assert submission.action == "hold_for_runtime_adapter"
    assert "PACKAGE_WARNING_PROPAGATED" in {finding.code for finding in submission.findings}


def test_three_builds_are_identical_non_mutating_and_canonical(tmp_path: Path) -> None:
    chain = _chain(tmp_path, "single_unit", (0,))
    originals = copy.deepcopy(chain[:3])
    builds = tuple(_build(chain) for _ in range(3))
    assert builds[0] == builds[1] == builds[2]
    assert builds[0].to_json() == builds[1].to_json() == builds[2].to_json()
    assert chain[:3] == originals
    assert re.fullmatch(r"[0-9a-f]{64}", builds[0].runtime_submission_package_fingerprint)
    assert all(re.fullmatch(r"[0-9a-f]{64}", unit.runtime_submission_unit_fingerprint) for unit in builds[0].units)
    payload = json.loads(builds[0].to_json())
    without_self = {key: value for key, value in payload.items() if key != "runtime_submission_package_fingerprint"}
    assert payload["runtime_submission_package_fingerprint"] not in json.dumps(without_self)
    assert "approval_statement" not in builds[0].to_json()
    assert "timestamp" not in payload and "uuid" not in payload


@pytest.mark.parametrize(("target", "field", "value", "expected"), [
    ("package", "execution_package_fingerprint", "0" * 64, RuntimeSubmissionConsistencyError),
    ("decision", "package_fingerprint", "0" * 64, RuntimeSubmissionConsistencyError),
    ("decision", "authorization_fingerprint", "0" * 64, RuntimeSubmissionConsistencyError),
    ("record", "package_fingerprint", "0" * 64, RuntimeSubmissionConsistencyError),
    ("record", "authorization_fingerprint", "0" * 64, RuntimeSubmissionConsistencyError),
    ("record", "approval_record_fingerprint", "0" * 64, RuntimeSubmissionConsistencyError),
    ("record", "approved", False, RuntimeSubmissionConsistencyError),
    ("record", "decision", "denied", RuntimeSubmissionConsistencyError),
    ("record", "action", "reject", RuntimeSubmissionConsistencyError),
    ("record", "activation_gate", "wrong", RuntimeSubmissionConsistencyError),
    ("record", "provider_execution_authorized", False, RuntimeSubmissionPolicyError),
    ("record", "translation_execution_authorized", False, RuntimeSubmissionPolicyError),
    ("record", "runtime_submission_authorized", False, RuntimeSubmissionPolicyError),
    ("record", "automatic_retry_authorized", True, RuntimeSubmissionPolicyError),
    ("record", "automatic_fallback_authorized", True, RuntimeSubmissionPolicyError),
    ("record", "output_replacement_authorized", True, RuntimeSubmissionPolicyError),
])
def test_chain_approval_and_flags_fail_closed(tmp_path: Path, target, field, value, expected) -> None:
    package, decision, record, _ = _chain(tmp_path)
    values = {"package": package, "decision": decision, "record": record}
    values[target] = _corrupt(values[target], **{field: value})
    with pytest.raises(expected):
        ControlledRuntimeSubmissionBuilder().build(
            package=values["package"], authorization_decision=values["decision"],
            approval_record=values["record"]
        )


@pytest.mark.parametrize(("indices", "approval_type"), [
    ((), "selected_units"), ((0, 0), "selected_units"), ((1, 0), "selected_units"),
    ((999,), "single_unit"), ((0, 1), "single_unit"), ((0,), "full_package"),
])
def test_invalid_scope_fails_closed(tmp_path: Path, indices, approval_type) -> None:
    package, decision, record, _ = _chain(tmp_path)
    record = _corrupt(record, approval_type=approval_type,
                      approved_unit_indices=indices, approved_unit_count=len(indices))
    with pytest.raises((RuntimeSubmissionScopeError, RuntimeSubmissionConsistencyError)):
        ControlledRuntimeSubmissionBuilder().build(
            package=package, authorization_decision=decision, approval_record=record
        )


@pytest.mark.parametrize(("field", "value"), [
    ("status", "executed"), ("attempt_count", 1), ("provider_request_count", 1),
    ("translation_result_attached", True), ("text", "tampered"),
    ("execution_unit_fingerprint", "0" * 64), ("source_character_start", -1),
])
def test_executed_or_tampered_unit_fails_closed(tmp_path: Path, field, value) -> None:
    package, decision, record, _ = _chain(tmp_path)
    units = list(package.units)
    units[0] = _corrupt(units[0], **{field: value})
    package = _corrupt(package, units=tuple(units))
    with pytest.raises(RuntimeSubmissionConsistencyError):
        ControlledRuntimeSubmissionBuilder().build(
            package=package, authorization_decision=decision, approval_record=record
        )


@pytest.mark.parametrize("name", ["package", "authorization_decision", "approval_record"])
def test_invalid_public_input_types_are_distinct(tmp_path: Path, name: str) -> None:
    package, decision, record, _ = _chain(tmp_path)
    values = {"package": package, "authorization_decision": decision, "approval_record": record}
    values[name] = "invalid"
    with pytest.raises(InvalidRuntimeSubmissionInputError):
        ControlledRuntimeSubmissionBuilder().build(**values)