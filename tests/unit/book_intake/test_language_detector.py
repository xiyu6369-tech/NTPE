from __future__ import annotations

from dataclasses import is_dataclass

import pytest

from core.book_intake.language_detector import SourceLanguageDetector


# ── fixture ──────────────────────────────────────────────────────


@pytest.fixture
def detector() -> SourceLanguageDetector:
    return SourceLanguageDetector()


# ── Korean ───────────────────────────────────────────────────────


def test_korean_basic(detector: SourceLanguageDetector) -> None:
    text = "안녕하세요 반갑습니다 한국어 텍스트입니다"
    result = detector.detect(text)
    assert result.language == "ko"
    assert result.confidence == 95
    assert result.recommended_profile == "ko-zh-Hant"
    assert "Primary language: Korean." in result.summary


def test_korean_long(detector: SourceLanguageDetector) -> None:
    text = (
        "한국어 소설의 첫 장면입니다. 주인공은 어두운 방 안에서 깨어났다. "
        "창밖으로는 빗소리가 들려왔고, 그는 천천히 몸을 일으켰다. "
        "방 안에는 아무도 없었지만, 어딘가에서 들려오는 목소리에 귀를 기울였다. "
        "그 목소리는 점점 더 가까워지고 있었고, 그는 두려움에 떨기 시작했다."
    )
    result = detector.detect(text)
    assert result.language == "ko"
    assert result.confidence == 95
    assert result.recommended_profile == "ko-zh-Hant"


def test_korean_with_punctuation(detector: SourceLanguageDetector) -> None:
    text = "안녕하세요! 이것은, 테스트입니다."
    result = detector.detect(text)
    assert result.language == "ko"


def test_korean_script_statistics(detector: SourceLanguageDetector) -> None:
    text = "한글만 있는 텍스트"
    result = detector.detect(text)
    stats = dict(result.script_statistics)
    assert "hangul" in stats
    assert stats["hangul"] > 0


# ── Japanese ─────────────────────────────────────────────────────


def test_japanese_basic(detector: SourceLanguageDetector) -> None:
    text = "こんにちは これは日本語のテストです"
    result = detector.detect(text)
    assert result.language == "ja"
    assert result.confidence == 95
    assert result.recommended_profile == "ja-zh-Hant"
    assert "Primary language: Japanese." in result.summary


def test_japanese_hiragana_only(detector: SourceLanguageDetector) -> None:
    text = "あいうえお かきくけこ さしすせそ"
    result = detector.detect(text)
    assert result.language == "ja"
    assert result.confidence == 95


def test_japanese_katakana_only(detector: SourceLanguageDetector) -> None:
    text = "アイウエオ カキクケコ サシスセソ"
    result = detector.detect(text)
    assert result.language == "ja"
    assert result.confidence == 95


def test_japanese_mixed_kana(detector: SourceLanguageDetector) -> None:
    text = "これは日本語です コンピューターを使ってテストします"
    result = detector.detect(text)
    assert result.language == "ja"


def test_japanese_with_kanji(detector: SourceLanguageDetector) -> None:
    text = "私は日本語の小説を読んでいます。主人公は暗い部屋で目を覚ました。"
    result = detector.detect(text)
    assert result.language == "ja"
    # Must not be misclassified as Chinese despite having CJK characters
    assert result.language != "zh"
    assert result.recommended_profile == "ja-zh-Hant"


def test_japanese_script_statistics(detector: SourceLanguageDetector) -> None:
    text = "これはテストです カタカナも含む"
    result = detector.detect(text)
    stats = dict(result.script_statistics)
    assert "hiragana" in stats or "katakana" in stats


# ── Chinese ──────────────────────────────────────────────────────


def test_chinese_basic(detector: SourceLanguageDetector) -> None:
    text = "你好這是中文測試文本歡迎使用"
    result = detector.detect(text)
    assert result.language == "zh"
    assert result.confidence == 95
    assert result.recommended_profile == "zh-Hant-zh-Hans"
    assert "Primary language: Chinese." in result.summary


def test_chinese_traditional(detector: SourceLanguageDetector) -> None:
    text = "繁體中文測試。主角在黑暗的房間裡醒來，窗外傳來雨聲。"
    result = detector.detect(text)
    assert result.language == "zh"


def test_chinese_simplified(detector: SourceLanguageDetector) -> None:
    text = "简体中文测试。主角在黑暗的房间里醒来，窗外传来雨声。"
    result = detector.detect(text)
    assert result.language == "zh"


def test_chinese_not_misclassified_as_japanese(detector: SourceLanguageDetector) -> None:
    text = "你好這是純中文沒有假名也沒有韓文只有漢字標點和數字123"
    result = detector.detect(text)
    assert result.language == "zh"
    assert result.language != "ja"
    assert result.language != "ko"


def test_chinese_script_statistics(detector: SourceLanguageDetector) -> None:
    text = "純中文測試文本"
    result = detector.detect(text)
    stats = dict(result.script_statistics)
    assert "cjk" in stats
    assert stats["cjk"] > 0


# ── English ──────────────────────────────────────────────────────


def test_english_basic(detector: SourceLanguageDetector) -> None:
    text = "Hello this is an English test sentence with multiple words"
    result = detector.detect(text)
    assert result.language == "en"
    assert result.confidence == 95
    assert result.recommended_profile == "en-zh-Hant"
    assert "Primary language: English." in result.summary


def test_english_paragraph(detector: SourceLanguageDetector) -> None:
    text = (
        "The protagonist awoke in a dark room. Rain pattered against the window. "
        "He slowly rose from the bed, his eyes adjusting to the dim light. "
        "A voice echoed from somewhere in the distance, drawing nearer."
    )
    result = detector.detect(text)
    assert result.language == "en"


def test_english_with_numbers(detector: SourceLanguageDetector) -> None:
    text = "This is test number 12345 with some digits 67890"
    result = detector.detect(text)
    assert result.language == "en"


def test_english_script_statistics(detector: SourceLanguageDetector) -> None:
    text = "Hello World"
    result = detector.detect(text)
    stats = dict(result.script_statistics)
    assert "latin" in stats
    assert stats["latin"] > 0


# ── Mixed ────────────────────────────────────────────────────────


def test_mixed_ko_en(detector: SourceLanguageDetector) -> None:
    text = (
        "안녕하세요 Hello everyone this is mixed content 한국어와 English가 섞여있습니다 "
        "이렇게 여러 언어가 혼합된 텍스트를 테스트합니다"
    )
    result = detector.detect(text)
    assert result.language == "mixed"
    assert result.confidence == 70
    assert result.recommended_profile == "ko-zh-Hant"
    assert "Mixed" in result.summary
    assert "Korean" in result.summary
    assert "English" in result.summary


def test_mixed_ja_en(detector: SourceLanguageDetector) -> None:
    text = (
        "こんにちは Hello this is Japanese and English mixed text "
        "日本語とEnglishが混ざった文章です テスト用のテキスト"
    )
    result = detector.detect(text)
    assert result.language == "mixed"
    assert result.confidence == 70
    assert result.recommended_profile == "ja-zh-Hant"
    assert "Mixed" in result.summary


def test_mixed_zh_en(detector: SourceLanguageDetector) -> None:
    text = (
        "你好這是中文和英文混和的測試 Hello this is mixed Chinese and English "
        "我們需要確認這樣的文本能被正確偵測 mixed content detection test"
    )
    result = detector.detect(text)
    assert result.language == "mixed"
    assert result.confidence == 70
    assert result.recommended_profile == "zh-Hant-zh-Hans"
    assert "Mixed" in result.summary


def test_not_mixed_with_few_english_words(detector: SourceLanguageDetector) -> None:
    """A Korean novel with a few English loanwords should NOT be classified as mixed."""
    text = (
        "한국어 소설의 긴 문장들입니다. 등장인물은 iPhone을 꺼내들었다. "
        "그는 computer 앞에 앉아 email을 확인했다. 이 문장은 대부분 한국어로 "
        "이루어져 있으며 소수의 영어 단어만 포함되어 있습니다. 소설의 전개는 "
        "한국어로 계속됩니다. 주인공은 서둘러 방을 나섰고, 거리는 어두웠다."
    )
    result = detector.detect(text)
    assert result.language == "ko"
    assert result.language != "mixed"


def test_not_mixed_with_few_japanese_loanwords(detector: SourceLanguageDetector) -> None:
    """A Chinese text with occasional English should not be mixed."""
    text = (
        "這是中文小說的第一章。主人公拿起一本book翻了翻。"
        "窗外的雨聲讓他想起了一個story。這裡面的內容很豐富，"
        "涵蓋許多情感和故事。中文為主的小說不應該因為幾個英文字就被判為mixed。"
    )
    result = detector.detect(text)
    assert result.language == "zh"
    assert result.language != "mixed"


# ── Unknown ──────────────────────────────────────────────────────


def test_unknown_empty(detector: SourceLanguageDetector) -> None:
    result = detector.detect("")
    assert result.language == "unknown"
    assert result.confidence == 0
    assert result.recommended_profile == "unknown"
    assert "empty" in result.summary.lower()


def test_unknown_whitespace_only(detector: SourceLanguageDetector) -> None:
    result = detector.detect("   \n\t  \n   ")
    assert result.language == "unknown"
    assert result.confidence == 0


def test_unknown_emoji_only(detector: SourceLanguageDetector) -> None:
    text = "😀😃😄😁😅😂🤣😊😇🙂🙃😉😌😍🥰😘😗😋😚😛😜🤪😝🤑🤗🤭🤫🤔🤐🤨😐😑"
    result = detector.detect(text)
    assert result.language == "unknown"
    assert result.confidence <= 30


def test_unknown_numbers_only(detector: SourceLanguageDetector) -> None:
    text = "1234567890 42 3.14159 2024 100 200 300 400 500"
    result = detector.detect(text)
    assert result.language == "unknown"
    assert result.confidence <= 30


def test_unknown_symbols_only(detector: SourceLanguageDetector) -> None:
    text = "!@#$%^&*()_+-=[]{}|;:',.<>?/~`\"\\"
    result = detector.detect(text)
    assert result.language == "unknown"
    assert result.confidence <= 30


# ── Confidence ───────────────────────────────────────────────────


def test_confidence_primary_is_95(detector: SourceLanguageDetector) -> None:
    assert detector.detect("안녕하세요 한국어").confidence == 95
    assert detector.detect("こんにちは日本語").confidence == 95
    assert detector.detect("你好中文測試").confidence == 95
    assert detector.detect("Hello English test").confidence == 95


def test_confidence_mixed_is_70(detector: SourceLanguageDetector) -> None:
    result = detector.detect(
        "안녕하세요 Hello this is mixed language text for testing confidence value"
    )
    assert result.confidence == 70


def test_confidence_unknown_range(detector: SourceLanguageDetector) -> None:
    result = detector.detect("😀😃😄😁")
    assert result.confidence <= 30
    assert result.confidence >= 0


# ── Recommended Profile ──────────────────────────────────────────


def test_recommended_profile_ko(detector: SourceLanguageDetector) -> None:
    assert detector.detect("안녕하세요 한국어").recommended_profile == "ko-zh-Hant"


def test_recommended_profile_ja(detector: SourceLanguageDetector) -> None:
    assert detector.detect("こんにちは日本語").recommended_profile == "ja-zh-Hant"


def test_recommended_profile_zh(detector: SourceLanguageDetector) -> None:
    assert detector.detect("你好中文測試").recommended_profile == "zh-Hant-zh-Hans"


def test_recommended_profile_en(detector: SourceLanguageDetector) -> None:
    assert detector.detect("Hello English").recommended_profile == "en-zh-Hant"


def test_recommended_profile_mixed_ko_en(detector: SourceLanguageDetector) -> None:
    result = detector.detect(
        "안녕하세요 Hello mixed Korean English text for profile recommendation"
    )
    assert result.recommended_profile == "ko-zh-Hant"


def test_recommended_profile_mixed_ja_en(detector: SourceLanguageDetector) -> None:
    result = detector.detect(
        "こんにちは Hello mixed Japanese English text for profile test"
    )
    assert result.recommended_profile == "ja-zh-Hant"


def test_recommended_profile_unknown(detector: SourceLanguageDetector) -> None:
    assert detector.detect("").recommended_profile == "unknown"
    assert detector.detect("😀😃").recommended_profile == "unknown"
    assert detector.detect("12345").recommended_profile == "unknown"


# ── Immutable ────────────────────────────────────────────────────


def test_result_is_dataclass(detector: SourceLanguageDetector) -> None:
    result = detector.detect("test")
    assert is_dataclass(result)
    assert is_dataclass(type(result))


def test_result_is_frozen(detector: SourceLanguageDetector) -> None:
    result = detector.detect("한글")
    with pytest.raises(Exception):
        result.language = "en"  # type: ignore[misc]


def test_script_statistics_is_tuple(detector: SourceLanguageDetector) -> None:
    result = detector.detect("한글")
    assert isinstance(result.script_statistics, tuple)


# ── Edge cases ───────────────────────────────────────────────────


def test_single_hangul_char(detector: SourceLanguageDetector) -> None:
    result = detector.detect("한")
    assert result.language == "ko"


def test_single_hiragana_char(detector: SourceLanguageDetector) -> None:
    result = detector.detect("あ")
    assert result.language == "ja"


def test_single_katakana_char(detector: SourceLanguageDetector) -> None:
    result = detector.detect("ア")
    assert result.language == "ja"


def test_single_cjk_char(detector: SourceLanguageDetector) -> None:
    result = detector.detect("漢")
    assert result.language == "zh"


def test_single_latin_char(detector: SourceLanguageDetector) -> None:
    result = detector.detect("A")
    assert result.language == "en"


def test_script_statistics_ordered(detector: SourceLanguageDetector) -> None:
    """script_statistics tuple order must be deterministic: hangul, hiragana, katakana, cjk, latin, other."""
    text = "한글 漢字 あいう English"
    result = detector.detect(text)
    names = [name for name, _ in result.script_statistics]
    expected_order = ["hangul", "hiragana", "katakana", "cjk", "latin", "other"]
    # Verify that each name present appears in the expected order
    prev_idx = -1
    for name in names:
        idx = expected_order.index(name)
        assert idx > prev_idx, f"'{name}' is out of order in script_statistics"
        prev_idx = idx


def test_ja_detected_before_zh(detector: SourceLanguageDetector) -> None:
    """Japanese text with kana + kanji must be ja, not zh."""
    text = "私は日本語を勉強しています毎日漢字を書きます"
    result = detector.detect(text)
    assert result.language == "ja"
    assert result.language != "zh"


def test_ko_detected_before_zh(detector: SourceLanguageDetector) -> None:
    """Korean text with hangul + some hanja(which fall in CJK) must be ko, not zh."""
    text = "한국어 테스트입니다 漢字도 조금 포함되어 있습니다"
    result = detector.detect(text)
    # Korean has hangul; CJK hanja characters exist but hangul dominates
    assert result.language == "ko"