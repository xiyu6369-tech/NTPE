from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from core.translation_execution_approval import (
    ExecutionApprovalFinding,
    ExecutionApprovalRecord,
    ExplicitHumanApprovalRequest,
)


def _request() -> ExplicitHumanApprovalRequest:
    return ExplicitHumanApprovalRequest(
        approval_type="single_unit",
        approved_package_fingerprint="1" * 64,
        approved_authorization_fingerprint="2" * 64,
        approved_unit_indices=(0,),
        approve_provider_execution=True,
        approve_translation_execution=True,
        approve_runtime_submission=True,
        approve_automatic_retry=False,
        approve_automatic_fallback=False,
        approve_output_replacement=False,
        approval_statement="APPROVE_CONTROLLED_TRANSLATION_EXECUTION: single_unit",
        approval_reference="manual-approval-001",
    )


def _record() -> ExecutionApprovalRecord:
    finding = ExecutionApprovalFinding("CODE", "info", "message")
    return ExecutionApprovalRecord(
        schema_name="ntpe.translation_execution_approval_record",
        schema_version="1.0",
        strategy="explicit_human_scoped_execution_approval_v1",
        activation_gate="translation_execution_explicitly_approved",
        package_fingerprint="1" * 64,
        authorization_fingerprint="2" * 64,
        approval_type="single_unit",
        approved_unit_indices=(0,),
        approved_unit_count=1,
        provider_execution_authorized=True,
        translation_execution_authorized=True,
        runtime_submission_authorized=True,
        automatic_retry_authorized=False,
        automatic_fallback_authorized=False,
        output_replacement_authorized=False,
        approved=True,
        decision="approved",
        action="eligible_for_controlled_runtime",
        approval_statement_fingerprint="3" * 64,
        approval_reference="manual-approval-001",
        findings=(finding,),
        summary="summary",
        approval_record_fingerprint="4" * 64,
    )


def test_request_record_and_finding_are_frozen_tuple_models() -> None:
    request = _request()
    record = _record()
    finding = record.findings[0]
    assert isinstance(request.approved_unit_indices, tuple)
    assert isinstance(record.approved_unit_indices, tuple)
    assert isinstance(record.findings, tuple)
    for target, name, value in (
        (request, "approval_type", "full_package"),
        (record, "approved", False),
        (finding, "message", "changed"),
    ):
        with pytest.raises(FrozenInstanceError):
            setattr(target, name, value)


def test_request_rejects_mutable_scope() -> None:
    with pytest.raises(TypeError):
        ExplicitHumanApprovalRequest(
            **{
                **_request().__dict__,
                "approved_unit_indices": [0],
            }
        )


def test_record_serialization_is_detached_and_deterministic() -> None:
    record = _record()
    payload = record.to_dict()
    assert json.loads(record.to_json()) == payload
    payload["approved_unit_indices"].append(4)
    payload["findings"][0]["message"] = "changed"
    assert record.approved_unit_indices == (0,)
    assert record.findings[0].message == "message"
