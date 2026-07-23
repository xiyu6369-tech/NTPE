from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from core.controlled_runtime_execution_authorization import (
    ControlledRuntimeExecutionAuthorizationRequest,
)
from core.controlled_runtime_execution_authorization.policy import (
    REQUEST_SCHEMA_NAME,
    REQUEST_SCHEMA_VERSION,
    exact_authorization_scope,
)
from verification.controlled_runtime.controlled_runtime_stage54_freeze_acceptance import (
    build_offline_chain,
)


def build_plan(tmp_path: Path):
    source = tmp_path / "stage61.txt"
    source.write_text(
        "Chapter 1\n"
        + "Controlled authorization text. " * 180
        + "\nChapter 2\n"
        + "Final text. " * 120,
        encoding="utf-8",
    )
    return build_offline_chain(source)[-1]


def build_request(plan, **changes):
    index = plan.selected_adapter_unit_indices[0]
    request = ControlledRuntimeExecutionAuthorizationRequest(
        authorization_id="stage61-caller-authorization",
        execution_plan_fingerprint=plan.execution_plan_fingerprint,
        selected_adapter_index=index,
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
            plan.execution_plan_fingerprint, index
        ),
        purpose="Authorize one frozen plan for controlled execution review.",
        schema_name=REQUEST_SCHEMA_NAME,
        schema_version=REQUEST_SCHEMA_VERSION,
    )
    return replace(request, **changes)

