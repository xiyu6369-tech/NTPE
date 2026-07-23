from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import replace
from pathlib import Path

import pytest

from core.book_preparation import BookPreparationProcessor
from core.translation_execution_approval import (
    ExecutionApprovalConsistencyError,
    ExecutionApprovalFinding,
    ExecutionApprovalPolicyError,
    ExecutionApprovalScopeError,
    ExplicitHumanApprovalRequest,
    InvalidExecutionApprovalInputError,
    InvalidHumanApprovalRequestError,
    TranslationExecutionApprover,
)
from core.translation_execution_approval.approver import _record_fingerprint
from core.translation_execution_authorization import (
    TranslationExecutionAuthorizationEvaluator,
)
from core.translation_execution_package import TranslationExecutionPackageBuilder


def _package_and_decision(tmp_path: Path, *, warning: bool = False):
    text = (
        "Chapter 1\n" + "Sentence. " * 300
        + "\nChapter 2\n" + "More sentence. " * 300
        if warning
        else "Chapter 1\n" + "Sentence. " * 180
        + "\nChapter 2\n" + "Another sentence. " * 110
    )
    path = tmp_path / ("warning.txt" if warning else "ready.txt")
    path.write_bytes(text.encode("utf-8"))
    package = TranslationExecutionPackageBuilder().build(
        BookPreparationProcessor().prepare(path)
    )
    decision = TranslationExecutionAuthorizationEvaluator().evaluate(package)
    assert package.status == ("prepared_with_warnings" if warning else "prepared")
    return package, decision, text


def _request(package, decision, approval_type="full_package", indices=None, **changes):
    if indices is None:
        indices = tuple(range(package.unit_count))
    values = {
        "approval_type": approval_type,
        "approved_package_fingerprint": package.execution_package_fingerprint,
        "approved_authorization_fingerprint": decision.authorization_fingerprint,
        "approved_unit_indices": indices,
        "approve_provider_execution": True,
        "approve_translation_execution": True,
        "approve_runtime_submission": True,
        "approve_automatic_retry": False,
        "approve_automatic_fallback": False,
        "approve_output_replacement": False,
        "approval_statement": "APPROVE_CONTROLLED_TRANSLATION_EXECUTION: full_package",
        "approval_reference": "manual-approval-001",
    }
    values.update(changes)
    return ExplicitHumanApprovalRequest(**values)


def _corrupt(target, **changes):
    candidate = copy.copy(target)
    for name, value in changes.items():
        object.__setattr__(candidate, name, value)
    return candidate


def _with_unit(package, **changes):
    units = list(package.units)
    units[0] = _corrupt(units[0], **changes)
    return _corrupt(package, units=tuple(units))


@pytest.mark.parametrize(
    ("approval_type", "indices"),
    [
        ("full_package", None),
        ("single_unit", (0,)),
        ("selected_units", (0, 1)),
    ],
)
def test_explicit_scoped_approval_succeeds(
    tmp_path: Path, approval_type: str, indices: tuple[int, ...] | None
) -> None:
    package, decision, _ = _package_and_decision(tmp_path)
    if indices is not None and max(indices) >= package.unit_count:
        indices = tuple(range(min(2, package.unit_count)))
    request = _request(package, decision, approval_type, indices)
    original_package = copy.deepcopy(package)
    original_decision = copy.deepcopy(decision)
    record = TranslationExecutionApprover().approve(
        package=package,
        authorization_decision=decision,
        approval_request=request,
    )
    assert (record.approved, record.decision, record.action) == (
        True,
        "approved",
        "eligible_for_controlled_runtime",
    )
    assert (
        record.provider_execution_authorized,
        record.translation_execution_authorized,
        record.runtime_submission_authorized,
    ) == (True, True, True)
    assert not any(
        (
            record.automatic_retry_authorized,
            record.automatic_fallback_authorized,
            record.output_replacement_authorized,
        )
    )
    assert record.approved_unit_indices == request.approved_unit_indices
    assert record.approved_unit_count == len(request.approved_unit_indices)
    assert record.package_fingerprint == package.execution_package_fingerprint
    assert record.authorization_fingerprint == decision.authorization_fingerprint
    assert package == original_package and decision == original_decision


@pytest.mark.parametrize(
    ("changes", "code"),
    [
        ({"approval_statement": ""}, "APPROVAL_STATEMENT_MISSING"),
        ({"approval_statement": "   "}, "APPROVAL_STATEMENT_MISSING"),
        ({"approval_statement": "this statement is long enough"}, "APPROVAL_CONFIRMATION_TOKEN_MISSING"),
        ({"approval_statement": "APPROVE"}, "APPROVAL_STATEMENT_MISSING"),
        ({"approval_reference": ""}, "APPROVAL_REFERENCE_MISSING"),
        ({"approval_reference": "   "}, "APPROVAL_REFERENCE_MISSING"),
        ({"approval_reference": "C:\\secret\\approval"}, "APPROVAL_REFERENCE_INVALID"),
        ({"approval_reference": "123e4567-e89b-12d3-a456-426614174000"}, "APPROVAL_REFERENCE_INVALID"),
    ],
)
def test_statement_and_reference_fail_closed(
    tmp_path: Path, changes: dict[str, object], code: str
) -> None:
    package, decision, _ = _package_and_decision(tmp_path)
    with pytest.raises(InvalidHumanApprovalRequestError) as captured:
        TranslationExecutionApprover().approve(
            package=package,
            authorization_decision=decision,
            approval_request=_request(package, decision, **changes),
        )
    assert captured.value.finding.code == code


def test_statement_fingerprint_preserves_exact_utf8_whitespace_and_newlines(
    tmp_path: Path,
) -> None:
    package, decision, _ = _package_and_decision(tmp_path)
    statements = (
        "APPROVE_CONTROLLED_TRANSLATION_EXECUTION: 中文批准",
        " APPROVE_CONTROLLED_TRANSLATION_EXECUTION: 中文批准",
        "APPROVE_CONTROLLED_TRANSLATION_EXECUTION:\n中文批准",
    )
    records = tuple(
        TranslationExecutionApprover().approve(
            package=package,
            authorization_decision=decision,
            approval_request=_request(
                package,
                decision,
                approval_statement=statement,
                approval_reference=f"manual-approval-{index}",
            ),
        )
        for index, statement in enumerate(statements)
    )
    assert tuple(
        item.approval_statement_fingerprint for item in records
    ) == tuple(hashlib.sha256(item.encode("utf-8")).hexdigest() for item in statements)
    assert len({item.approval_statement_fingerprint for item in records}) == 3
    assert all(statement not in record.to_json() for statement, record in zip(statements, records))


def test_warning_package_requires_and_records_acknowledgement(tmp_path: Path) -> None:
    package, decision, _ = _package_and_decision(tmp_path, warning=True)
    with pytest.raises(InvalidHumanApprovalRequestError) as captured:
        TranslationExecutionApprover().approve(
            package=package,
            authorization_decision=decision,
            approval_request=_request(package, decision),
        )
    assert captured.value.finding.code == "PACKAGE_WARNING_ACKNOWLEDGEMENT_REQUIRED"
    request = _request(
        package,
        decision,
        approval_statement=(
            "APPROVE_CONTROLLED_TRANSLATION_EXECUTION:\n"
            "ACKNOWLEDGE_PACKAGE_WARNINGS:\nfull_package"
        ),
    )
    record = TranslationExecutionApprover().approve(
        package=package,
        authorization_decision=decision,
        approval_request=request,
    )
    assert "PACKAGE_WARNING_ACKNOWLEDGED" in {
        finding.code for finding in record.findings
    }


@pytest.mark.parametrize(
    ("approval_type", "indices", "code"),
    [
        ("invalid", (0,), "APPROVAL_TYPE_INVALID"),
        ("selected_units", (), "APPROVAL_SCOPE_EMPTY"),
        ("selected_units", (0, 0), "APPROVAL_SCOPE_DUPLICATE_INDEX"),
        ("selected_units", (1, 0), "APPROVAL_SCOPE_UNSORTED"),
        ("selected_units", (-1,), "APPROVAL_SCOPE_OUT_OF_RANGE"),
        ("selected_units", (999,), "APPROVAL_SCOPE_OUT_OF_RANGE"),
        ("selected_units", (True,), "APPROVAL_SCOPE_TYPE_MISMATCH"),
        ("selected_units", ("0",), "APPROVAL_SCOPE_TYPE_MISMATCH"),
        ("full_package", (0,), "FULL_PACKAGE_SCOPE_INCOMPLETE"),
        ("single_unit", (0, 1), "SINGLE_UNIT_SCOPE_INVALID"),
    ],
)
def test_invalid_scope_is_rejected(
    tmp_path: Path, approval_type: str, indices: tuple[object, ...], code: str
) -> None:
    package, decision, _ = _package_and_decision(tmp_path)
    if code == "FULL_PACKAGE_SCOPE_INCOMPLETE" and package.unit_count == 1:
        pytest.skip("fixture produced a single unit")
    with pytest.raises(ExecutionApprovalScopeError) as captured:
        TranslationExecutionApprover().approve(
            package=package,
            authorization_decision=decision,
            approval_request=_request(package, decision, approval_type, indices),
        )
    assert captured.value.finding.code == code


@pytest.mark.parametrize(
    ("decision_changes", "code"),
    [
        ({"package_fingerprint": "1" * 64}, "PACKAGE_FINGERPRINT_MISMATCH"),
        ({"authorization_fingerprint": "1" * 64}, "AUTHORIZATION_FINGERPRINT_MISMATCH"),
        ({"authorized": True, "decision": "authorized"}, "AUTHORIZATION_DECISION_INVALID"),
        ({"requires_human_approval": False}, "AUTHORIZATION_HUMAN_APPROVAL_NOT_REQUIRED"),
        ({"package_status": "blocked"}, "AUTHORIZATION_DECISION_INVALID"),
        ({"package_action": "reject"}, "AUTHORIZATION_DECISION_INVALID"),
    ],
)
def test_noncanonical_authorization_decision_is_rejected(
    tmp_path: Path, decision_changes: dict[str, object], code: str
) -> None:
    package, decision, _ = _package_and_decision(tmp_path)
    candidate = _corrupt(decision, **decision_changes)
    with pytest.raises(ExecutionApprovalConsistencyError) as captured:
        TranslationExecutionApprover().approve(
            package=package,
            authorization_decision=candidate,
            approval_request=_request(package, decision),
        )
    assert captured.value.finding.code == code


@pytest.mark.parametrize(
    ("unit_changes", "package_changes", "code"),
    [
        ({"status": "running"}, {}, "PACKAGE_ALREADY_EXECUTED"),
        ({"attempt_count": 1}, {}, "PACKAGE_ALREADY_EXECUTED"),
        ({"provider_request_count": 1}, {}, "PACKAGE_ALREADY_EXECUTED"),
        ({"translation_result_attached": True}, {}, "PACKAGE_ALREADY_EXECUTED"),
        ({}, {"provider_execution_authorized": True}, "PACKAGE_AUTHORIZATION_FLAG_TAMPERED"),
        ({}, {"status": "blocked", "action": "reject"}, "PACKAGE_STATE_INVALID"),
    ],
)
def test_tampered_or_executed_package_is_rejected(
    tmp_path: Path,
    unit_changes: dict[str, object],
    package_changes: dict[str, object],
    code: str,
) -> None:
    package, decision, _ = _package_and_decision(tmp_path)
    candidate = _with_unit(package, **unit_changes) if unit_changes else package
    candidate = _corrupt(candidate, **package_changes) if package_changes else candidate
    with pytest.raises(ExecutionApprovalConsistencyError) as captured:
        TranslationExecutionApprover().approve(
            package=candidate,
            authorization_decision=decision,
            approval_request=_request(package, decision),
        )
    assert captured.value.finding.code == code


@pytest.mark.parametrize(
    ("field", "code"),
    [
        ("approve_automatic_retry", "RETRY_AUTHORIZATION_REJECTED"),
        ("approve_automatic_fallback", "FALLBACK_AUTHORIZATION_REJECTED"),
        ("approve_output_replacement", "OUTPUT_REPLACEMENT_AUTHORIZATION_REJECTED"),
    ],
)
def test_prohibited_authorization_flags_are_rejected(
    tmp_path: Path, field: str, code: str
) -> None:
    package, decision, _ = _package_and_decision(tmp_path)
    with pytest.raises(ExecutionApprovalPolicyError) as captured:
        TranslationExecutionApprover().approve(
            package=package,
            authorization_decision=decision,
            approval_request=_request(package, decision, **{field: True}),
        )
    assert captured.value.finding.code == code


@pytest.mark.parametrize(
    "field",
    [
        "approve_provider_execution",
        "approve_translation_execution",
        "approve_runtime_submission",
    ],
)
def test_all_controlled_execution_flags_are_required(
    tmp_path: Path, field: str
) -> None:
    package, decision, _ = _package_and_decision(tmp_path)
    with pytest.raises(InvalidHumanApprovalRequestError) as captured:
        TranslationExecutionApprover().approve(
            package=package,
            authorization_decision=decision,
            approval_request=_request(package, decision, **{field: False}),
        )
    assert captured.value.finding.code == "CONTROLLED_EXECUTION_AUTHORIZATION_INCOMPLETE"


def test_record_fingerprint_serialization_and_three_runs_are_deterministic(
    tmp_path: Path,
) -> None:
    package, decision, text = _package_and_decision(tmp_path)
    request = _request(package, decision)
    approver = TranslationExecutionApprover()
    records = tuple(
        approver.approve(
            package=package,
            authorization_decision=decision,
            approval_request=request,
        )
        for _ in range(3)
    )
    assert records[0] == records[1] == records[2]
    assert re.fullmatch(r"[0-9a-f]{64}", records[0].approval_record_fingerprint)
    assert json.loads(records[0].to_json()) == records[0].to_dict()
    assert text not in records[0].to_json()
    assert request.approval_statement not in records[0].to_json()
    payload = records[0].to_dict()
    observed = payload.pop("approval_record_fingerprint")
    assert observed not in json.dumps(payload, ensure_ascii=False)

    changed_scope = replace(request, approval_type="single_unit", approved_unit_indices=(0,))
    changed_reference = replace(request, approval_reference="manual-approval-002")
    variants = (
        approver.approve(
            package=package,
            authorization_decision=decision,
            approval_request=changed_scope,
        ),
        approver.approve(
            package=package,
            authorization_decision=decision,
            approval_request=changed_reference,
        ),
    )
    assert all(
        variant.approval_record_fingerprint != records[0].approval_record_fingerprint
        for variant in variants
    )


def test_authorization_findings_and_utf8_reference_affect_record_fingerprint(
    tmp_path: Path,
) -> None:
    package, decision, _ = _package_and_decision(tmp_path)
    request = _request(
        package,
        decision,
        approval_reference="人工批准-001",
    )
    record = TranslationExecutionApprover().approve(
        package=package,
        authorization_decision=decision,
        approval_request=request,
    )
    assert "人工批准-001" in record.to_json()
    assert "\\u4eba" not in record.to_json()

    changed_authorization = _record_fingerprint(
        package_fingerprint=record.package_fingerprint,
        authorization_fingerprint="a" * 64,
        request=request,
        statement_fingerprint=record.approval_statement_fingerprint,
        findings=record.findings,
    )
    changed_findings = _record_fingerprint(
        package_fingerprint=record.package_fingerprint,
        authorization_fingerprint=record.authorization_fingerprint,
        request=request,
        statement_fingerprint=record.approval_statement_fingerprint,
        findings=record.findings
        + (ExecutionApprovalFinding("EXTRA", "info", "extra"),),
    )
    assert changed_authorization != record.approval_record_fingerprint
    assert changed_findings != record.approval_record_fingerprint

def test_invalid_api_input_types_are_rejected(tmp_path: Path) -> None:
    package, decision, _ = _package_and_decision(tmp_path)
    request = _request(package, decision)
    approver = TranslationExecutionApprover()
    for kwargs in (
        {"package": "bad", "authorization_decision": decision, "approval_request": request},
        {"package": package, "authorization_decision": "bad", "approval_request": request},
        {"package": package, "authorization_decision": decision, "approval_request": "bad"},
    ):
        with pytest.raises(InvalidExecutionApprovalInputError):
            approver.approve(**kwargs)
