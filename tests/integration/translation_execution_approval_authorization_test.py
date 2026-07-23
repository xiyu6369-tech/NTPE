from __future__ import annotations

import copy
from pathlib import Path

import pytest

from core.book_preparation import BookPreparationProcessor
from core.translation_execution_approval import (
    ExplicitHumanApprovalRequest,
    TranslationExecutionApprover,
)
from core.translation_execution_authorization import (
    TranslationExecutionAuthorizationEvaluator,
)
from core.translation_execution_package import TranslationExecutionPackageBuilder


@pytest.mark.parametrize(
    "text",
    [
        "제1장\n" + "한국어 문장입니다. " * 180 + "\n제2장\n" + "다음 문장입니다. " * 180,
        "第一章\n" + "這是中文小說內容。" * 190 + "\n第二章\n" + "下一章內容。" * 220,
        "第一章\n" + "これは日本語の小説です。" * 180 + "\n第二章\n" + "次の章です。" * 220,
        "Chapter 1\r\n" + "English novel text. " * 140 + "\r\nChapter 2\r\n" + "Final text. " * 180,
    ],
)
def test_real_offline_pipeline_produces_scoped_approval_record(
    tmp_path: Path, text: str
) -> None:
    source = tmp_path / "novel.txt"
    source.write_bytes(text.encode("utf-8"))
    package = TranslationExecutionPackageBuilder().build(
        BookPreparationProcessor().prepare(source)
    )
    decision = TranslationExecutionAuthorizationEvaluator().evaluate(package)
    request = ExplicitHumanApprovalRequest(
        approval_type="full_package",
        approved_package_fingerprint=package.execution_package_fingerprint,
        approved_authorization_fingerprint=decision.authorization_fingerprint,
        approved_unit_indices=tuple(range(package.unit_count)),
        approve_provider_execution=True,
        approve_translation_execution=True,
        approve_runtime_submission=True,
        approve_automatic_retry=False,
        approve_automatic_fallback=False,
        approve_output_replacement=False,
        approval_statement=(
            "APPROVE_CONTROLLED_TRANSLATION_EXECUTION:\n"
            "ACKNOWLEDGE_PACKAGE_WARNINGS:\nfull_package"
        ),
        approval_reference="controlled-canary-request-01",
    )
    record = TranslationExecutionApprover().approve(
        package=package,
        authorization_decision=decision,
        approval_request=request,
    )
    assert record.approved is True
    assert record.approved_unit_count == package.unit_count
    assert text not in record.to_json()


def test_approval_is_offline_write_free_deterministic_and_non_mutating(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = "Chapter 1\n" + "Sentence. " * 180 + "\nChapter 2\n" + "More. " * 300
    source = tmp_path / "novel.txt"
    source.write_bytes(text.encode("utf-8"))
    package = TranslationExecutionPackageBuilder().build(
        BookPreparationProcessor().prepare(source)
    )
    decision = TranslationExecutionAuthorizationEvaluator().evaluate(package)
    request = ExplicitHumanApprovalRequest(
        approval_type="selected_units",
        approved_package_fingerprint=package.execution_package_fingerprint,
        approved_authorization_fingerprint=decision.authorization_fingerprint,
        approved_unit_indices=(0,),
        approve_provider_execution=True,
        approve_translation_execution=True,
        approve_runtime_submission=True,
        approve_automatic_retry=False,
        approve_automatic_fallback=False,
        approve_output_replacement=False,
        approval_statement="APPROVE_CONTROLLED_TRANSLATION_EXECUTION: selected_units",
        approval_reference="user-approved-stage43",
    )
    original_package = copy.deepcopy(package)
    original_decision = copy.deepcopy(decision)
    before = {item.relative_to(tmp_path) for item in tmp_path.rglob("*")}

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("network/provider/runtime boundary invoked")

    monkeypatch.setattr("socket.create_connection", forbidden)
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
    assert package == original_package and decision == original_decision
    assert before == after
    assert all(unit.status == "prepared" for unit in package.units)
    assert all(unit.attempt_count == 0 for unit in package.units)
    assert all(unit.provider_request_count == 0 for unit in package.units)
    assert records[0].automatic_retry_authorized is False
    assert records[0].automatic_fallback_authorized is False
    assert records[0].output_replacement_authorized is False
