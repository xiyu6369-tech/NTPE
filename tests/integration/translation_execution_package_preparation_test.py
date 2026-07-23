from __future__ import annotations

from pathlib import Path

import pytest

from core.book_intake import get_book_intake_freeze_metadata
from core.book_preparation import (
    BookPreparationProcessor,
    get_book_preparation_freeze_metadata,
)
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
def test_frozen_preparation_to_execution_package_is_lossless(
    tmp_path: Path, text: str
) -> None:
    source = tmp_path / "novel.txt"
    source.write_bytes(text.encode("utf-8"))
    preparation = BookPreparationProcessor().prepare(source)
    package = TranslationExecutionPackageBuilder().build(preparation)
    assert package.reconstruct_source_text() == preparation.reconstruct_text() == text
    assert package.unit_count == preparation.chunk_plan.chunk_count
    assert package.coverage_ratio == 1.0
    assert package.action == "hold_for_execution_authorization"


def test_builder_consumes_frozen_gates_and_performs_no_execution_or_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = "Chapter 1\n" + "Sentence. " * 180 + "\nChapter 2\n" + "More. " * 300
    source = tmp_path / "novel.txt"
    source.write_bytes(text.encode("utf-8"))
    preparation = BookPreparationProcessor().prepare(source)
    before = {item.relative_to(tmp_path) for item in tmp_path.rglob("*")}

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("network/provider/runtime boundary invoked")

    monkeypatch.setattr("socket.create_connection", forbidden)
    packages = tuple(
        TranslationExecutionPackageBuilder().build(preparation) for _ in range(3)
    )
    after = {item.relative_to(tmp_path) for item in tmp_path.rglob("*")}

    assert get_book_intake_freeze_metadata().activation_gate == "book_intake_layer_frozen"
    assert (
        get_book_preparation_freeze_metadata().activation_gate
        == "book_preparation_pipeline_frozen"
    )
    assert packages[0] == packages[1] == packages[2]
    assert before == after
    assert sum(unit.provider_request_count for unit in packages[0].units) == 0
    assert packages[0].translation_execution_authorized is False
    assert packages[0].runtime_submission_authorized is False
    assert packages[0].automatic_retry_authorized is False
    assert packages[0].automatic_fallback_authorized is False
    assert packages[0].output_replacement_authorized is False

