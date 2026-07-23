from __future__ import annotations

import copy
import socket
from pathlib import Path

import pytest

from core.controlled_runtime_execution_authorization import (
    ControlledRuntimeExecutionAuthorizationRequest,
    ControlledRuntimeExecutionAuthorizer,
)
from core.controlled_runtime_execution_authorization.policy import (
    REQUEST_SCHEMA_NAME,
    REQUEST_SCHEMA_VERSION,
    exact_authorization_scope,
)
from core.controlled_runtime_execution_plan import (
    get_controlled_runtime_preparation_freeze_metadata,
    validate_controlled_runtime_preparation_freeze,
)
from verification.controlled_runtime.controlled_runtime_stage54_freeze_acceptance import (
    build_offline_chain,
)


@pytest.mark.parametrize(
    "text",
    [
        "第一章\r\n" + "明示授權內容。  " * 180 + "\r\n第二章\r\n" + "結尾。" * 110,
        "제1장\n" + "명시적 승인 문장입니다. " * 180 + "\n제2장\n" + "끝입니다. " * 110,
        "Chapter 1\r\n" + "Explicit authorization. " * 180 + "\r\nChapter 2\r\n" + "End. " * 110,
    ],
)
def test_authentic_stage53_plan_and_stage54_freeze_authorize_without_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    text: str,
) -> None:
    source = tmp_path / "novel.txt"
    source.write_bytes(text.encode("utf-8"))
    chain = build_offline_chain(source)
    plan = chain[-1]
    original = copy.deepcopy(chain)
    selected = plan.selected_adapter_unit_indices[0]
    request = ControlledRuntimeExecutionAuthorizationRequest(
        authorization_id="stage61-integration-authorization",
        execution_plan_fingerprint=plan.execution_plan_fingerprint,
        selected_adapter_index=selected,
        requested_provider_request_limit=1,
        requested_translation_request_limit=1,
        retry_requested=False,
        fallback_requested=False,
        output_replacement_requested=False,
        runtime_execution_requested=True,
        provider_execution_requested=True,
        network_execution_requested=True,
        translation_execution_requested=True,
        caller_confirmation=True,
        authorization_scope=exact_authorization_scope(
            plan.execution_plan_fingerprint, selected
        ),
        purpose="Stage 6.1 authentic frozen-chain authorization.",
        schema_name=REQUEST_SCHEMA_NAME,
        schema_version=REQUEST_SCHEMA_VERSION,
    )

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("runtime/provider/network boundary invoked")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    before = {path.relative_to(tmp_path) for path in tmp_path.rglob("*")}
    assert validate_controlled_runtime_preparation_freeze().valid
    result = ControlledRuntimeExecutionAuthorizer().authorize(
        request=request,
        execution_plan=plan,
        freeze_metadata=get_controlled_runtime_preparation_freeze_metadata(),
    )
    after = {path.relative_to(tmp_path) for path in tmp_path.rglob("*")}
    assert result.status == "authorized_not_executed"
    assert result.decision.authorized
    assert not result.decision.runtime_execution_enabled
    assert not result.decision.provider_execution_enabled
    assert not result.decision.network_execution_enabled
    assert not result.decision.translation_execution_enabled
    assert not result.decision.authorization_consumed
    assert not result.decision.authorization_reusable
    assert not any(
        (
            result.runtime_invoked,
            result.provider_invoked,
            result.network_invoked,
            result.translation_invoked,
            result.output_written,
            result.resume_written,
            result.cache_written,
            result.retry_used,
            result.fallback_used,
            result.production_hook_invoked,
        )
    )
    assert chain == original
    assert before == after


def test_rejection_is_deterministic_and_does_not_modify_stage5_objects(
    tmp_path: Path,
) -> None:
    source = tmp_path / "reject.txt"
    source.write_text("Chapter 1\n" + "Sentence. " * 300, encoding="utf-8")
    chain = build_offline_chain(source)
    plan = chain[-1]
    original = copy.deepcopy(chain)
    index = plan.selected_adapter_unit_indices[0]
    request = ControlledRuntimeExecutionAuthorizationRequest(
        authorization_id="stage61-rejected-authorization",
        execution_plan_fingerprint=plan.execution_plan_fingerprint,
        selected_adapter_index=index,
        requested_provider_request_limit=1,
        requested_translation_request_limit=1,
        retry_requested=True,
        fallback_requested=False,
        output_replacement_requested=False,
        runtime_execution_requested=True,
        provider_execution_requested=True,
        network_execution_requested=True,
        translation_execution_requested=True,
        caller_confirmation=True,
        authorization_scope=exact_authorization_scope(
            plan.execution_plan_fingerprint, index
        ),
        purpose="Deterministic rejection.",
        schema_name=REQUEST_SCHEMA_NAME,
        schema_version=REQUEST_SCHEMA_VERSION,
    )
    results = tuple(
        ControlledRuntimeExecutionAuthorizer().authorize(
            request=request,
            execution_plan=plan,
            freeze_metadata=get_controlled_runtime_preparation_freeze_metadata(),
        )
        for _ in range(3)
    )
    assert results[0] == results[1] == results[2]
    assert results[0].status == "rejected"
    assert not results[0].decision.authorized
    assert chain == original
