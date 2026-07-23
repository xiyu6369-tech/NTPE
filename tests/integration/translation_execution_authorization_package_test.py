from __future__ import annotations

import copy
from pathlib import Path

import pytest

from core.book_preparation import BookPreparationProcessor
from core.translation_execution_authorization import TranslationExecutionAuthorizationEvaluator
from core.translation_execution_package import TranslationExecutionPackageBuilder


@pytest.mark.parametrize(
    "text",
    [
        "제1장\n" + "한국어 문장입니다. " * 160 + "\n제2장\n" + "다음 문장입니다. " * 160,
        "第一章\n" + "這是中文小說內容。" * 180 + "\n第二章\n" + "下一章內容。" * 220,
        "第一章\n" + "これは日本語の小説です。" * 160 + "\n第二章\n" + "次の章です。" * 220,
        "Chapter 1\r\n" + "English novel text. " * 120 + "\r\nChapter 2\r\n" + "Final text. " * 180 + "\r\n",
    ],
)
def test_package_to_decision_is_denied_without_copying_content(
    tmp_path: Path, text: str
) -> None:
    source = tmp_path / "novel.txt"
    source.write_bytes(text.encode("utf-8"))
    package = TranslationExecutionPackageBuilder().build(
        BookPreparationProcessor().prepare(source)
    )
    decision = TranslationExecutionAuthorizationEvaluator().evaluate(package)
    assert decision.authorized is False
    assert decision.decision == "denied"
    assert decision.package_fingerprint == package.execution_package_fingerprint
    assert text not in decision.to_json()


def test_evaluation_is_offline_write_free_deterministic_and_non_mutating(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = "Chapter 1\n" + "Sentence. " * 180 + "\nChapter 2\n" + "More. " * 300
    source = tmp_path / "novel.txt"
    source.write_bytes(text.encode("utf-8"))
    package = TranslationExecutionPackageBuilder().build(
        BookPreparationProcessor().prepare(source)
    )
    original = copy.deepcopy(package)
    before = {item.relative_to(tmp_path) for item in tmp_path.rglob("*")}

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("network/provider/runtime boundary invoked")

    monkeypatch.setattr("socket.create_connection", forbidden)
    decisions = tuple(
        TranslationExecutionAuthorizationEvaluator().evaluate(package)
        for _ in range(3)
    )
    after = {item.relative_to(tmp_path) for item in tmp_path.rglob("*")}

    assert decisions[0] == decisions[1] == decisions[2]
    assert package == original
    assert before == after
    assert all(unit.status == "prepared" for unit in package.units)
    assert all(unit.attempt_count == 0 for unit in package.units)
    assert all(unit.provider_request_count == 0 for unit in package.units)
    assert decisions[0].runtime_submission_authorized is False
    assert decisions[0].automatic_retry_authorized is False
    assert decisions[0].automatic_fallback_authorized is False
    assert decisions[0].output_replacement_authorized is False

