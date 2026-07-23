from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import pytest

from core.book_preparation import BookPreparationProcessor
from core.translation_execution_approval import (
    ExecutionApprovalConsistencyError,
    ExecutionApprovalScopeError,
    ExplicitHumanApprovalRequest,
    TranslationExecutionApprover,
    get_translation_execution_governance_freeze_metadata,
    validate_translation_execution_governance_freeze,
)
from core.translation_execution_authorization import (
    TranslationExecutionAuthorizationEvaluator,
)
from core.translation_execution_package import TranslationExecutionPackageBuilder


def _pipeline(path: Path):
    preparation = BookPreparationProcessor().prepare(path)
    package = TranslationExecutionPackageBuilder().build(preparation)
    decision = TranslationExecutionAuthorizationEvaluator().evaluate(package)
    return preparation, package, decision


def _request(package, decision, approval_type: str):
    indices = {
        "single_unit": (0,),
        "selected_units": tuple(range(min(2, package.unit_count))),
        "full_package": tuple(range(package.unit_count)),
    }[approval_type]
    warning_token = (
        "\nACKNOWLEDGE_PACKAGE_WARNINGS"
        if package.status == "prepared_with_warnings"
        else ""
    )
    statement = (
        f"APPROVE_CONTROLLED_TRANSLATION_EXECUTION{warning_token}\n{approval_type}"
    )
    return ExplicitHumanApprovalRequest(
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
        approval_reference=f"stage44-{approval_type}",
    )


@pytest.mark.parametrize(
    ("approval_type", "text"),
    [
        (
            "single_unit",
            "Chapter 1\r\n" + "English text. " * 160 + "\r\nChapter 2\r\n" + "End. " * 160,
        ),
        (
            "selected_units",
            "第一章\n" + "繁體中文與日本語の多語內容。" * 320 + "\n第二章\n" + "後續內容。" * 320,
        ),
        (
            "full_package",
            "Chapter 1\n" + "Warning fixture. " * 300 + "\nChapter 2\n" + "More. " * 300,
        ),
    ],
    ids=("single-crlf", "selected-unicode", "full-warning"),
)
def test_frozen_pipeline_is_deterministic_scoped_and_execution_free(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    approval_type: str,
    text: str,
) -> None:
    source = tmp_path / f"{approval_type}.txt"
    source.write_bytes(text.encode("utf-8"))

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("provider, network, translation, or runtime was invoked")

    monkeypatch.setattr("socket.create_connection", forbidden)
    runs = tuple(_pipeline(source) for _ in range(3))
    assert runs[0] == runs[1] == runs[2]
    preparation, package, decision = runs[0]
    assert preparation.reconstruct_text() == text
    assert package.reconstruct_source_text() == text
    assert package.unit_count == len(preparation.translation_chunks)
    assert decision.authorized is False
    assert decision.requires_human_approval is True
    assert decision.package_fingerprint == package.execution_package_fingerprint
    assert not any(
        (
            decision.provider_execution_authorized,
            decision.translation_execution_authorized,
            decision.runtime_submission_authorized,
            decision.automatic_retry_authorized,
            decision.automatic_fallback_authorized,
            decision.output_replacement_authorized,
        )
    )

    request = _request(package, decision, approval_type)
    original_package = copy.deepcopy(package)
    original_decision = copy.deepcopy(decision)
    before = {item.relative_to(tmp_path) for item in tmp_path.rglob("*")}
    records = tuple(
        TranslationExecutionApprover().approve(
            package=package,
            authorization_decision=decision,
            approval_request=request,
        )
        for _ in range(3)
    )
    after = {item.relative_to(tmp_path) for item in tmp_path.rglob("*")}
    assert records[0] == records[1] == records[2]
    record = records[0]
    assert package == original_package and decision == original_decision
    assert before == after
    assert record.approved_unit_indices == request.approved_unit_indices
    assert record.package_fingerprint == package.execution_package_fingerprint
    assert record.authorization_fingerprint == decision.authorization_fingerprint
    assert record.approval_statement_fingerprint == hashlib.sha256(
        request.approval_statement.encode("utf-8")
    ).hexdigest()
    assert request.approval_statement not in record.to_json()
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
    assert all(unit.status == "prepared" for unit in package.units)
    assert all(unit.attempt_count == 0 for unit in package.units)
    assert all(unit.provider_request_count == 0 for unit in package.units)
    assert all(unit.translation_result_attached is False for unit in package.units)


def test_scope_and_tampering_remain_fail_closed(tmp_path: Path) -> None:
    source = tmp_path / "scope.txt"
    source.write_text(
        "Chapter 1\n" + "Sentence. " * 240 + "\nChapter 2\n" + "More. " * 240,
        encoding="utf-8",
    )
    _, package, decision = _pipeline(source)
    duplicate = _request(package, decision, "selected_units")
    object.__setattr__(duplicate, "approved_unit_indices", (0, 0))
    with pytest.raises(ExecutionApprovalScopeError):
        TranslationExecutionApprover().approve(
            package=package,
            authorization_decision=decision,
            approval_request=duplicate,
        )

    tampered = copy.copy(package)
    object.__setattr__(tampered, "provider_execution_authorized", True)
    with pytest.raises(ExecutionApprovalConsistencyError):
        TranslationExecutionApprover().approve(
            package=tampered,
            authorization_decision=decision,
            approval_request=_request(package, decision, "full_package"),
        )


def test_freeze_metadata_and_validation_repeat_identically() -> None:
    metadata = tuple(
        get_translation_execution_governance_freeze_metadata() for _ in range(3)
    )
    results = tuple(validate_translation_execution_governance_freeze() for _ in range(3))
    assert metadata[0] == metadata[1] == metadata[2]
    assert results[0] == results[1] == results[2]
    assert results[0].valid is True
