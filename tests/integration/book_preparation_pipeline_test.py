from __future__ import annotations

from pathlib import Path

import pytest

from core.book_preparation import BookPreparationProcessor


@pytest.mark.parametrize(
    "text",
    [
        "제1장\n" + "한국어 문장입니다. " * 100,
        "第一章\n" + "這是中文小說內容。" * 100,
        "第一章\n" + "これは日本語の小説です。" * 100,
        "Chapter 1\n" + "This is an English novel sentence. " * 100,
        "  Chapter 1  \r\n" + "e\u0301 text with spaces. " * 100 + "\r\n",
    ],
)
def test_real_pipeline_preserves_multilingual_text_exactly(tmp_path: Path, text: str) -> None:
    path = tmp_path / "novel.txt"
    path.write_bytes(text.encode("utf-8"))
    result = BookPreparationProcessor().prepare(path)
    assert result.reconstruct_text() == text
    assert result.intake_result.text == text
    assert result.segmentation_result.reconstruct_text() == text
    assert result.chunk_plan.reconstruct_text() == text


def test_real_pipeline_is_offline_write_free_and_deterministic(tmp_path: Path, monkeypatch) -> None:
    text = "Chapter 1\n" + "Sentence one. Sentence two.\n\n" * 100
    path = tmp_path / "novel.txt"
    path.write_bytes(text.encode("utf-8"))
    before = {item.relative_to(tmp_path) for item in tmp_path.rglob("*")}

    def forbidden(*args, **kwargs):
        raise AssertionError("network/provider/translation boundary must not be invoked")

    monkeypatch.setattr("socket.create_connection", forbidden)
    results = [BookPreparationProcessor().prepare(path) for _ in range(3)]
    after = {item.relative_to(tmp_path) for item in tmp_path.rglob("*")}

    assert results[0] == results[1] == results[2]
    assert results[0].reconstruct_text() == text
    assert before == after
