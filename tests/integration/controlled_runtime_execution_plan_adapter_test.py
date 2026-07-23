from __future__ import annotations

import copy
from pathlib import Path

import pytest

from core.book_preparation import BookPreparationProcessor
from core.controlled_runtime_adapter import ControlledRuntimeAdapter
from core.controlled_runtime_execution_plan import (
    ControlledRuntimeExecutionPlanner,
)
from core.controlled_runtime_submission import ControlledRuntimeSubmissionBuilder
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
        "第一章\r\n" + "中文內容與空白。  " * 180 + "\r\n第二章\r\n" + "結尾。" * 110 + "\r\n",
        "제1장\n" + "한국어 문장입니다. " * 180 + "\n제2장\n" + "끝입니다. " * 110 + "\n",
        "第一章\n" + "日本語の小説です。e\u0301 " * 180 + "\n第二章\n" + "終わりです。" * 110 + "\n",
        "Chapter 1\r\n" + "English text. " * 180 + "\r\nChapter 2\r\n" + "The end. " * 110 + "\r\n",
    ],
)
def test_real_pipeline_plans_one_explicit_unit_without_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    text: str,
) -> None:
    source = tmp_path / "novel.txt"
    source.write_bytes(text.encode("utf-8"))
    package = TranslationExecutionPackageBuilder().build(
        BookPreparationProcessor().prepare(source)
    )
    decision = TranslationExecutionAuthorizationEvaluator().evaluate(package)
    statement = "APPROVE_CONTROLLED_TRANSLATION_EXECUTION: plan integration"
    if package.status == "prepared_with_warnings":
        statement += " ACKNOWLEDGE_PACKAGE_WARNINGS"
    approval_request = ExplicitHumanApprovalRequest(
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
        approval_statement=statement,
        approval_reference="stage53-integration",
    )
    record = TranslationExecutionApprover().approve(
        package=package,
        authorization_decision=decision,
        approval_request=approval_request,
    )
    submission = ControlledRuntimeSubmissionBuilder().build(
        package=package,
        authorization_decision=decision,
        approval_record=record,
    )
    adapter_result = ControlledRuntimeAdapter().prepare(
        submission_package=submission
    )
    original = copy.deepcopy(adapter_result)
    before = {path.relative_to(tmp_path) for path in tmp_path.rglob("*")}

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("runtime/provider/network boundary invoked")

    monkeypatch.setattr("socket.create_connection", forbidden)
    plans = tuple(
        ControlledRuntimeExecutionPlanner().plan(
            adapter_preparation_result=adapter_result,
            selected_adapter_unit_indices=(0,),
        )
        for _ in range(3)
    )
    after = {path.relative_to(tmp_path) for path in tmp_path.rglob("*")}
    assert plans[0] == plans[1] == plans[2]
    assert (
        plans[0].reconstruct_planned_text()
        == adapter_result.request.units[0].text
    )
    assert adapter_result == original
    assert before == after
    assert not plans[0].execution_started
    assert not plans[0].execution_completed
    assert plans[0].provider_requests_executed == 0
    assert plans[0].translation_executions_completed == 0
