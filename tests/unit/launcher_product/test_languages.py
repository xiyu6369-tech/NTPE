from __future__ import annotations

from core.launcher_product.languages import MAX_SAMPLE_BYTES, detect_source_language, inspect_text_file


def test_detects_korean_sample() -> None:
    result = detect_source_language("그는 조용히 문을 열고 방 안으로 들어갔다.")
    assert result.language == "ko"
    assert result.ambiguous is False


def test_detects_japanese_sample() -> None:
    result = detect_source_language("彼女は静かにドアを開けました。こんにちは。")
    assert result.language == "ja"
    assert result.ambiguous is False


def test_detects_english_sample() -> None:
    result = detect_source_language("The old house stood quietly beneath the winter moon.")
    assert result.language == "en"
    assert result.ambiguous is False


def test_mixed_language_sample_is_ambiguous() -> None:
    result = detect_source_language("安寧 가나 abcd 世界")
    assert result.language == "unknown"
    assert result.ambiguous is True


def test_cjk_only_sample_is_ambiguous() -> None:
    result = detect_source_language("天地玄黃宇宙洪荒")
    assert result.language == "unknown"
    assert result.ambiguous is True


def test_empty_input_is_ambiguous() -> None:
    result = detect_source_language("")
    assert (result.language, result.confidence, result.ambiguous) == ("unknown", 0.0, True)


def test_corrupt_decode_is_reported(tmp_path) -> None:
    source = tmp_path / "broken.txt"
    source.write_bytes(b"\xff\xfe\x00\xd8")
    inspection = inspect_text_file(source)
    assert inspection.readable is False
    assert inspection.error_message


def test_file_sampling_is_bounded(tmp_path) -> None:
    source = tmp_path / "novel.txt"
    source.write_text("한국어 문장입니다.\n" * 20_000, encoding="utf-8")
    inspection = inspect_text_file(source)
    assert inspection.readable is True
    assert inspection.sampled_bytes == MAX_SAMPLE_BYTES
    assert inspection.truncated_sample is True
    assert inspection.detection.language == "ko"
