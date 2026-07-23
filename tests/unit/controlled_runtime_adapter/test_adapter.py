from __future__ import annotations

import copy
import json
import re
from dataclasses import replace
from pathlib import Path

import pytest

from core.book_preparation import BookPreparationProcessor
from core.controlled_runtime_adapter import (
    ControlledRuntimeAdapter,
    InvalidRuntimeAdapterInputError,
    RuntimeAdapterCapabilityError,
    RuntimeAdapterConsistencyError,
)
from core.controlled_runtime_adapter.policy import DEFAULT_CAPABILITY_PROFILE
from core.controlled_runtime_submission import ControlledRuntimeSubmissionBuilder
from core.translation_execution_approval import (
    ExplicitHumanApprovalRequest,
    TranslationExecutionApprover,
)
from core.translation_execution_authorization import (
    TranslationExecutionAuthorizationEvaluator,
)
from core.translation_execution_package import TranslationExecutionPackageBuilder


def _corrupt(target, **changes):
    candidate = copy.copy(target)
    for name, value in changes.items():
        object.__setattr__(candidate, name, value)
    return candidate


def _submission(
    tmp_path: Path,
    *,
    approval_type: str = "full_package",
    indices: tuple[int, ...] | None = None,
    warning: bool = False,
):
    text = (
        "Chapter 1\n"
        + "Sentence. " * 300
        + "\nChapter 2\n"
        + "More sentence. " * 300
        if warning
        else "Chapter 1\n"
        + "Sentence. " * 180
        + "\nChapter 2\n"
        + "Another sentence. " * 110
    )
    source = tmp_path / "novel.txt"
    source.write_bytes(text.encode("utf-8"))
    package = TranslationExecutionPackageBuilder().build(
        BookPreparationProcessor().prepare(source)
    )
    decision = TranslationExecutionAuthorizationEvaluator().evaluate(package)
    indices = tuple(range(package.unit_count)) if indices is None else indices
    statement = "APPROVE_CONTROLLED_TRANSLATION_EXECUTION: adapter scope"
    if package.status == "prepared_with_warnings":
        statement += " ACKNOWLEDGE_PACKAGE_WARNINGS"
    approval_request = ExplicitHumanApprovalRequest(
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
        approval_reference="stage52-unit-test",
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
    return submission, text


def test_full_submission_maps_one_to_one_and_preserves_authorization(
    tmp_path: Path,
) -> None:
    submission, text = _submission(tmp_path)
    result = ControlledRuntimeAdapter().prepare(
        submission_package=submission
    )
    request = result.request
    assert request.adapter_unit_count == submission.submission_unit_count
    assert request.approved_unit_indices == submission.approved_unit_indices
    assert request.reconstruct_approved_text() == text
    assert request.is_full_package_request
    for index, (adapter_unit, submission_unit) in enumerate(
        zip(request.units, submission.units)
    ):
        assert adapter_unit.adapter_unit_index == index
        assert adapter_unit.submission_index == submission_unit.submission_index
        assert (
            adapter_unit.execution_unit_index
            == submission_unit.execution_unit_index
        )
        assert adapter_unit.execution_unit_id == submission_unit.execution_unit_id
        assert adapter_unit.text == submission_unit.text
        assert (
            adapter_unit.source_character_start
            == submission_unit.source_character_start
        )
        assert (
            adapter_unit.source_character_end
            == submission_unit.source_character_end
        )
        assert adapter_unit.section_indices == submission_unit.section_indices
        assert adapter_unit.heading_text == submission_unit.heading_text
        assert adapter_unit.boundary_reason == submission_unit.boundary_reason
        assert (
            adapter_unit.runtime_submission_unit_fingerprint
            == submission_unit.runtime_submission_unit_fingerprint
        )
        assert adapter_unit.status == "prepared_for_runtime_adapter"
        assert adapter_unit.runtime_attempt_count == 0
        assert adapter_unit.provider_request_count == 0
        assert adapter_unit.translation_result_attached is False
    assert (
        request.provider_execution_authorized,
        request.translation_execution_authorized,
        request.runtime_submission_authorized,
    ) == (True, True, True)
    assert not request.automatic_retry_authorized
    assert not request.automatic_fallback_authorized
    assert not request.output_replacement_authorized
    assert not request.runtime_submission_executed
    assert request.provider_requests_executed == 0
    assert request.translation_executions_completed == 0


def test_partial_scope_and_warning_semantics(tmp_path: Path) -> None:
    partial, _ = _submission(
        tmp_path,
        approval_type="single_unit",
        indices=(0,),
    )
    partial_result = ControlledRuntimeAdapter().prepare(
        submission_package=partial
    )
    assert partial_result.request.is_partial_scope_request
    assert partial_result.request.approved_unit_indices == (0,)
    assert "PARTIAL_SCOPE_ADAPTER_REQUEST" in {
        finding.code for finding in partial_result.findings
    }

    warning, _ = _submission(tmp_path, warning=True)
    warning_result = ControlledRuntimeAdapter().prepare(
        submission_package=warning
    )
    assert warning_result.status == "prepared_for_runtime_adapter_with_warnings"
    assert warning_result.action == "hold_for_controlled_runtime_execution_stage"
    assert "SUBMISSION_WARNING_PROPAGATED" in {
        finding.code for finding in warning_result.findings
    }


def test_preparation_is_compatible_but_never_invokes_execution(
    tmp_path: Path,
) -> None:
    submission, _ = _submission(tmp_path)
    result = ControlledRuntimeAdapter().prepare(
        submission_package=submission
    )
    assert result.prepared is True
    assert result.compatible is True
    assert result.runtime_invoked is False
    assert result.provider_invoked is False
    assert result.translation_invoked is False
    assert {finding.code for finding in result.findings} >= {
        "RUNTIME_ADAPTER_REQUEST_PREPARED",
        "RUNTIME_EXECUTION_NOT_PERFORMED",
        "PROVIDER_EXECUTION_NOT_PERFORMED",
        "TRANSLATION_EXECUTION_NOT_PERFORMED",
        "PROVIDER_CAPABILITY_NOT_AVAILABLE",
        "TRANSLATION_CAPABILITY_NOT_AVAILABLE",
    }
    assert not hasattr(ControlledRuntimeAdapter, "execute")
    assert not hasattr(ControlledRuntimeAdapter, "submit")
    assert not hasattr(ControlledRuntimeAdapter, "run")
    assert not hasattr(ControlledRuntimeAdapter, "translate")


def test_three_preparations_are_identical_non_mutating_and_serializable(
    tmp_path: Path,
) -> None:
    submission, _ = _submission(tmp_path)
    original = copy.deepcopy(submission)
    results = tuple(
        ControlledRuntimeAdapter().prepare(submission_package=submission)
        for _ in range(3)
    )
    assert results[0] == results[1] == results[2]
    assert results[0].to_json() == results[1].to_json() == results[2].to_json()
    assert submission == original
    assert re.fullmatch(
        r"[0-9a-f]{64}",
        results[0].request.runtime_adapter_request_fingerprint,
    )
    assert re.fullmatch(r"[0-9a-f]{64}", results[0].preparation_fingerprint)
    assert all(
        re.fullmatch(r"[0-9a-f]{64}", unit.runtime_adapter_unit_fingerprint)
        for unit in results[0].request.units
    )
    payload = json.loads(results[0].to_json())
    assert "approval_statement" not in results[0].to_json()
    assert "timestamp" not in payload
    assert "uuid" not in payload
    detached = results[0].to_dict()
    detached["request"]["units"][0]["text"] = "changed"
    assert results[0].request.units[0].text != "changed"


def test_stricter_profile_changes_fingerprint_and_preserves_compatible_scope(
    tmp_path: Path,
) -> None:
    submission, _ = _submission(tmp_path)
    default = ControlledRuntimeAdapter().prepare(
        submission_package=submission
    )
    stricter_profile = replace(
        DEFAULT_CAPABILITY_PROFILE,
        supports_partial_scope=False,
    )
    stricter = ControlledRuntimeAdapter(stricter_profile).prepare(
        submission_package=submission
    )
    assert stricter.prepared
    assert (
        stricter.request.runtime_adapter_request_fingerprint
        != default.request.runtime_adapter_request_fingerprint
    )
    partial, _ = _submission(
        tmp_path,
        approval_type="single_unit",
        indices=(0,),
    )
    with pytest.raises(RuntimeAdapterCapabilityError):
        ControlledRuntimeAdapter(stricter_profile).prepare(
            submission_package=partial
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_name", "wrong"),
        ("schema_version", "2.0"),
        ("strategy", "wrong"),
        ("activation_gate", "wrong"),
        ("runtime_submission_package_fingerprint", "0" * 64),
        ("status", "submitted"),
        ("action", "execute_now"),
        ("runtime_submission_executed", True),
        ("provider_requests_executed", 1),
        ("translation_executions_completed", 1),
        ("automatic_retry_authorized", True),
        ("automatic_fallback_authorized", True),
        ("output_replacement_authorized", True),
        ("approved_character_count", 1),
        ("approval_coverage_ratio", 0.5),
    ],
)
def test_submission_package_tampering_fails_closed(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    submission, _ = _submission(tmp_path)
    submission = _corrupt(submission, **{field: value})
    with pytest.raises(RuntimeAdapterConsistencyError):
        ControlledRuntimeAdapter().prepare(submission_package=submission)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("submission_index", 1),
        ("execution_unit_index", 999),
        ("text", "tampered"),
        ("source_character_start", -1),
        ("runtime_submission_unit_fingerprint", "0" * 64),
        ("status", "executed"),
        ("runtime_attempt_count", 1),
        ("provider_request_count", 1),
        ("translation_result_attached", True),
    ],
)
def test_submission_unit_tampering_fails_closed(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    submission, _ = _submission(tmp_path)
    units = list(submission.units)
    units[0] = _corrupt(units[0], **{field: value})
    submission = _corrupt(submission, units=tuple(units))
    with pytest.raises(RuntimeAdapterConsistencyError):
        ControlledRuntimeAdapter().prepare(submission_package=submission)


def test_source_chain_scope_count_and_findings_tampering_fails_closed(
    tmp_path: Path,
) -> None:
    submission, _ = _submission(tmp_path)
    variants = (
        _corrupt(
            submission,
            source=_corrupt(
                submission.source,
                source_content_fingerprint="0" * 64,
            ),
        ),
        _corrupt(submission, approved_unit_indices=(1, 0)),
        _corrupt(submission, submission_unit_count=999),
        _corrupt(submission, findings=()),
    )
    for candidate in variants:
        with pytest.raises(RuntimeAdapterConsistencyError):
            ControlledRuntimeAdapter().prepare(
                submission_package=candidate
            )


def test_invalid_input_type_is_distinct() -> None:
    with pytest.raises(InvalidRuntimeAdapterInputError):
        ControlledRuntimeAdapter().prepare(
            submission_package="invalid"  # type: ignore[arg-type]
        )
