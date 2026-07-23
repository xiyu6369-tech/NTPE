from __future__ import annotations

import copy
from dataclasses import replace
from pathlib import Path

import pytest

from core.controlled_runtime_adapter import (
    ControlledRuntimeAdapter,
    RuntimeAdapterCapabilityError,
)
from core.controlled_runtime_execution_plan import (
    ControlledRuntimeExecutionPlanner,
    ControlledRuntimeExecutionPolicyError,
    ControlledRuntimeExecutionScopeError,
    validate_controlled_runtime_preparation_freeze,
)
from core.controlled_runtime_execution_plan.policy import DEFAULT_POLICY
from verification.controlled_runtime.controlled_runtime_stage54_freeze_acceptance import (
    build_offline_chain,
)


@pytest.mark.parametrize(
    "text",
    [
        "第一章\r\n" + "中文內容與空白。  " * 180 + "\r\n第二章\r\n" + "結尾。" * 110 + "\r\n",
        "제1장\n" + "한국어 문장입니다. " * 180 + "\n제2장\n" + "끝입니다. " * 110 + "\n",
        "第一章\n" + "日本語の小説です。e\u0301 " * 180 + "\n第二章\n" + "終わりです。" * 110 + "\n",
        "Chapter 1\r\n" + "English text. " * 180 + "\r\nChapter 2\r\n" + "The end. " * 110 + "\r\n",
    ],
)
def test_frozen_pipeline_is_deterministic_offline_and_non_mutating(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    text: str,
) -> None:
    assert validate_controlled_runtime_preparation_freeze().valid
    source = tmp_path / "novel.txt"
    source.write_bytes(text.encode("utf-8"))

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("runtime/provider/network boundary invoked")

    monkeypatch.setattr("socket.create_connection", forbidden)
    chains = tuple(build_offline_chain(source) for _ in range(3))
    assert chains[0] == chains[1] == chains[2]
    package, decision, approval, submission, adapter_result, plan = chains[0]
    original = copy.deepcopy((submission, adapter_result))
    assert plan.reconstruct_planned_text() == adapter_result.request.units[0].text
    assert (
        package.execution_package_fingerprint
        == decision.package_fingerprint
        == approval.package_fingerprint
        == submission.source.execution_package_fingerprint
    )
    assert (
        submission.runtime_submission_package_fingerprint
        == adapter_result.request.source.runtime_submission_package_fingerprint
        == plan.source.runtime_submission_package_fingerprint
    )
    assert (
        adapter_result.request.runtime_adapter_request_fingerprint
        == plan.source.runtime_adapter_request_fingerprint
    )
    assert (
        adapter_result.preparation_fingerprint
        == plan.source.runtime_adapter_preparation_fingerprint
    )
    assert not adapter_result.runtime_invoked
    assert not adapter_result.provider_invoked
    assert not adapter_result.translation_invoked
    assert not plan.runtime_execution_enabled
    assert not plan.provider_execution_enabled
    assert not plan.translation_execution_enabled
    assert plan.provider_requests_executed == 0
    assert plan.translation_executions_completed == 0
    assert (submission, adapter_result) == original


def test_scope_capability_policy_and_fingerprint_tampering_fail_closed(
    tmp_path: Path,
) -> None:
    source = tmp_path / "novel.txt"
    source.write_text(
        "Chapter 1\n" + "Sentence. " * 180 + "\nChapter 2\n" + "Tail. " * 180,
        encoding="utf-8",
    )
    *_, adapter_result, _ = build_offline_chain(source)
    with pytest.raises(ControlledRuntimeExecutionScopeError):
        ControlledRuntimeExecutionPlanner().plan(
            adapter_preparation_result=adapter_result
        )
    with pytest.raises(RuntimeAdapterCapabilityError):
        ControlledRuntimeAdapter(
            replace(
                adapter_result.capability_profile,
                supports_provider_execution=True,
            )
        )
    with pytest.raises(ControlledRuntimeExecutionPolicyError):
        ControlledRuntimeExecutionPlanner(
            replace(DEFAULT_POLICY, allow_automatic_retry=True)
        )
    tampered = copy.copy(adapter_result)
    object.__setattr__(tampered, "preparation_fingerprint", "0" * 64)
    with pytest.raises(Exception):
        ControlledRuntimeExecutionPlanner().plan(
            adapter_preparation_result=tampered,
            selected_adapter_unit_indices=(0,),
        )
