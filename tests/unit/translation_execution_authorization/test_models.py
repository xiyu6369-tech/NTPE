from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from core.book_preparation import BookPreparationProcessor
from core.translation_execution_authorization import (
    ExecutionAuthorizationDecision,
    ExecutionAuthorizationFinding,
    TranslationExecutionAuthorizationEvaluator,
)
from core.translation_execution_package import TranslationExecutionPackageBuilder


def _decision(tmp_path: Path):
    text = "Chapter 1\n" + "Sentence. " * 180 + "\nChapter 2\n" + "More. " * 300
    path = tmp_path / "book.txt"
    path.write_bytes(text.encode("utf-8"))
    package = TranslationExecutionPackageBuilder().build(
        BookPreparationProcessor().prepare(path)
    )
    return TranslationExecutionAuthorizationEvaluator().evaluate(package), text


def test_decision_finding_and_policy_are_frozen(tmp_path: Path) -> None:
    decision, _ = _decision(tmp_path)
    finding = decision.findings[0]
    policy = TranslationExecutionAuthorizationEvaluator()._policy
    assert isinstance(decision, ExecutionAuthorizationDecision)
    assert isinstance(finding, ExecutionAuthorizationFinding)
    assert isinstance(decision.findings, tuple)
    for target, name, value in (
        (decision, "authorized", True),
        (finding, "message", "changed"),
        (policy, "allow_prepared", True),
    ):
        with pytest.raises(FrozenInstanceError):
            setattr(target, name, value)


def test_to_dict_is_detached_and_json_omits_package_text(tmp_path: Path) -> None:
    decision, text = _decision(tmp_path)
    payload = decision.to_dict()
    encoded = decision.to_json()
    assert json.loads(encoded) == payload
    assert text not in encoded
    payload["findings"][0]["message"] = "changed"
    payload["decision"] = "authorized"
    assert decision.findings[0].message != "changed"
    assert decision.decision == "denied"

