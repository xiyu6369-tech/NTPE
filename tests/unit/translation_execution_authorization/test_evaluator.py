from __future__ import annotations

import copy
import json
import re
from dataclasses import replace
from pathlib import Path

import pytest

from core.book_preparation import BookPreparationProcessor
from core.translation_execution_authorization import (
    ExecutionAuthorizationConsistencyError,
    InvalidExecutionAuthorizationInputError,
    InvalidExecutionPackageStateError,
    TranslationExecutionAuthorizationEvaluator,
)
from core.translation_execution_authorization.evaluator import _authorization_fingerprint
from core.translation_execution_authorization.policy import DEFAULT_POLICY
from core.translation_execution_package import TranslationExecutionPackageBuilder


def _package(tmp_path: Path, *, warning: bool = False):
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
    assert package.status == ("prepared_with_warnings" if warning else "prepared")
    return package, text


def _corrupt(target, **changes):
    candidate = copy.copy(target)
    for name, value in changes.items():
        object.__setattr__(candidate, name, value)
    return candidate


def _with_unit(package, index: int = 0, **changes):
    units = list(package.units)
    units[index] = _corrupt(units[index], **changes)
    return _corrupt(package, units=tuple(units))


def test_prepared_package_returns_complete_explicit_denial(tmp_path: Path) -> None:
    package, _ = _package(tmp_path)
    original = copy.deepcopy(package)
    decision = TranslationExecutionAuthorizationEvaluator().evaluate(package)
    assert (decision.authorized, decision.decision, decision.action) == (
        False, "denied", "hold_for_explicit_authorization"
    )
    assert decision.requires_human_approval is True
    assert (
        decision.package_fingerprint,
        decision.package_status,
        decision.package_action,
        decision.package_activation_gate,
    ) == (
        package.execution_package_fingerprint,
        package.status,
        package.action,
        package.activation_gate,
    )
    assert all(
        getattr(decision, name) is False
        for name in (
            "provider_execution_authorized",
            "translation_execution_authorized",
            "runtime_submission_authorized",
            "automatic_retry_authorized",
            "automatic_fallback_authorized",
            "output_replacement_authorized",
        )
    )
    codes = tuple(finding.code for finding in decision.findings)
    assert codes[:4] == (
        "EXPLICIT_AUTHORIZATION_REQUIRED",
        "PROVIDER_EXECUTION_NOT_AUTHORIZED",
        "TRANSLATION_EXECUTION_NOT_AUTHORIZED",
        "RUNTIME_SUBMISSION_NOT_AUTHORIZED",
    )
    assert package == original


def test_warning_package_is_denied_for_manual_review(tmp_path: Path) -> None:
    package, _ = _package(tmp_path, warning=True)
    decision = TranslationExecutionAuthorizationEvaluator().evaluate(package)
    assert decision.authorized is False
    assert decision.package_status == "prepared_with_warnings"
    assert decision.action == "manual_review"
    assert "MANUAL_REVIEW_REQUIRED" in {item.code for item in decision.findings}


def test_invalid_input_type_is_rejected() -> None:
    with pytest.raises(InvalidExecutionAuthorizationInputError):
        TranslationExecutionAuthorizationEvaluator().evaluate("package")


@pytest.mark.parametrize(
    ("changes", "code"),
    [
        ({"schema_name": "other"}, "PACKAGE_SCHEMA_MISMATCH"),
        ({"schema_version": "2.0"}, "PACKAGE_VERSION_MISMATCH"),
        ({"strategy": "other"}, "PACKAGE_STRATEGY_MISMATCH"),
        ({"activation_gate": "other"}, "PACKAGE_ACTIVATION_GATE_MISMATCH"),
        ({"status": "invalid"}, "PACKAGE_STATUS_NOT_ELIGIBLE"),
        ({"status": "manual_review"}, "PACKAGE_STATUS_NOT_ELIGIBLE"),
        ({"status": "blocked", "action": "reject"}, "BLOCKED_PACKAGE_REJECTED"),
        ({"action": "execute"}, "PACKAGE_ACTION_MISMATCH"),
    ],
)
def test_contract_and_state_tampering_fail_closed(
    tmp_path: Path, changes: dict[str, object], code: str
) -> None:
    package, _ = _package(tmp_path)
    with pytest.raises(InvalidExecutionPackageStateError) as captured:
        TranslationExecutionAuthorizationEvaluator().evaluate(_corrupt(package, **changes))
    assert captured.value.finding.code == code


def test_invalid_fingerprint_count_content_and_coverage_fail_closed(tmp_path: Path) -> None:
    package, _ = _package(tmp_path)
    cases = (
        (_corrupt(package, execution_package_fingerprint="g" * 64), "PACKAGE_FINGERPRINT_INVALID"),
        (_corrupt(package, unit_count=package.unit_count + 1), "PACKAGE_UNIT_COUNT_MISMATCH"),
        (_corrupt(package, character_count=package.character_count + 1), "PACKAGE_CONTENT_MISMATCH"),
        (_corrupt(package, coverage_ratio=0.9), "PACKAGE_CONTENT_MISMATCH"),
        (_with_unit(package, text="changed"), "PACKAGE_CONTENT_MISMATCH"),
    )
    for candidate, code in cases:
        with pytest.raises(ExecutionAuthorizationConsistencyError) as captured:
            TranslationExecutionAuthorizationEvaluator().evaluate(candidate)
        assert captured.value.finding.code == code


@pytest.mark.parametrize(
    "changes",
    [
        {"unit_id": "unit-000001-invalid"},
        {"non_whitespace_character_count": 0},
        {"source_chunk_fingerprint": "0" * 64},
    ],
)
def test_canonical_unit_content_metadata_fail_closed(
    tmp_path: Path, changes: dict[str, object]
) -> None:
    package, _ = _package(tmp_path)
    with pytest.raises(ExecutionAuthorizationConsistencyError) as captured:
        TranslationExecutionAuthorizationEvaluator().evaluate(
            _with_unit(package, **changes)
        )
    assert captured.value.finding.code == "PACKAGE_CONTENT_MISMATCH"

def test_gap_and_overlap_fail_closed(tmp_path: Path) -> None:
    package, _ = _package(tmp_path)
    assert package.unit_count >= 2
    cases = (
        (_with_unit(package, source_character_start=1), "PACKAGE_OFFSET_GAP"),
        (_with_unit(package, 1, source_character_start=package.units[1].source_character_start - 1), "PACKAGE_OFFSET_OVERLAP"),
    )
    for candidate, code in cases:
        with pytest.raises(ExecutionAuthorizationConsistencyError) as captured:
            TranslationExecutionAuthorizationEvaluator().evaluate(candidate)
        assert captured.value.finding.code == code


@pytest.mark.parametrize(
    ("changes", "code"),
    [
        ({"status": "running"}, "PACKAGE_ALREADY_EXECUTED"),
        ({"attempt_count": 1}, "PACKAGE_ALREADY_EXECUTED"),
        ({"provider_request_count": 1}, "PACKAGE_PROVIDER_REQUEST_DETECTED"),
        ({"translation_result_attached": True}, "PACKAGE_TRANSLATION_RESULT_DETECTED"),
    ],
)
def test_executed_or_result_bearing_units_fail_closed(
    tmp_path: Path, changes: dict[str, object], code: str
) -> None:
    package, _ = _package(tmp_path)
    with pytest.raises(InvalidExecutionPackageStateError) as captured:
        TranslationExecutionAuthorizationEvaluator().evaluate(_with_unit(package, **changes))
    assert captured.value.finding.code == code


@pytest.mark.parametrize(
    "field",
    [
        "provider_execution_authorized",
        "translation_execution_authorized",
        "runtime_submission_authorized",
        "automatic_retry_authorized",
        "automatic_fallback_authorized",
        "output_replacement_authorized",
    ],
)
def test_package_authorization_tampering_is_rejected(tmp_path: Path, field: str) -> None:
    package, _ = _package(tmp_path)
    with pytest.raises(InvalidExecutionPackageStateError) as captured:
        TranslationExecutionAuthorizationEvaluator().evaluate(
            _corrupt(package, **{field: True})
        )
    assert captured.value.finding.code == "PACKAGE_AUTHORIZATION_FLAG_TAMPERED"


def test_fingerprint_serialization_and_three_repetitions_are_deterministic(
    tmp_path: Path,
) -> None:
    package, text = _package(tmp_path)
    evaluator = TranslationExecutionAuthorizationEvaluator()
    decisions = tuple(evaluator.evaluate(package) for _ in range(3))
    assert decisions[0] == decisions[1] == decisions[2]
    assert re.fullmatch(r"[0-9a-f]{64}", decisions[0].authorization_fingerprint)
    assert json.loads(decisions[0].to_json()) == decisions[0].to_dict()
    assert text not in decisions[0].to_json()

    versioned = TranslationExecutionAuthorizationEvaluator(
        replace(DEFAULT_POLICY, policy_version="1.1-stricter")
    ).evaluate(package)
    assert versioned.authorization_fingerprint != decisions[0].authorization_fingerprint
    alternative = _authorization_fingerprint(
        package=package,
        policy=DEFAULT_POLICY,
        action="manual_review",
        findings=decisions[0].findings,
    )
    assert alternative != decisions[0].authorization_fingerprint
    payload = decisions[0].to_dict()
    observed = payload.pop("authorization_fingerprint")
    assert observed not in json.dumps(payload, ensure_ascii=False)


def test_utf8_serialization_has_no_path_or_environment_metadata(tmp_path: Path) -> None:
    package, _ = _package(tmp_path)
    policy = replace(DEFAULT_POLICY, policy_name="授權政策")
    encoded = TranslationExecutionAuthorizationEvaluator(policy).evaluate(package).to_json()
    assert "授權政策" in encoded and "\\u6388" not in encoded
    assert str(tmp_path) not in encoded
    assert "timestamp" not in encoded.lower() and "hostname" not in encoded.lower()
    assert not re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        encoded,
        re.IGNORECASE,
    )

