from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.translation_engine.context_intelligence import detect_unnatural_phrases
from lts.txt_translation_runtime import (
    TxtTranslationOptions,
    analyze_translation_quality,
    build_qa_retry_user_prompt,
)


def test_naturalness_guard_is_retry_worthy_and_feeds_retry_prompt() -> None:
    options = TxtTranslationOptions(
        input_path=Path("sample.txt"),
        output_dir=Path("output"),
        quality_profile="literary",
        min_length_ratio=0.0,
        max_korean_chars=0,
    )
    qa_report = analyze_translation_quality(
        "정태의는 숨을 삼켰다.",
        "鄭泰義嘔了一口氣。幾乎可以用十個手指頭就能數得過來。",
        options,
        locked_dictionary={},
    )
    naturalness = next(issue for issue in qa_report["issues"] if issue["code"] == "NATURALNESS_GUARD")
    retry_prompt = build_qa_retry_user_prompt("Translate the full passage.", qa_report, 2)

    assert qa_report["passed"] is False
    assert naturalness["severity"] == "error"
    assert naturalness["retry_worthy"] is True
    assert "Naturalness Guard repair directives" in retry_prompt
    assert "倒抽一口氣" in retry_prompt
    assert "十根手指就數得完" in retry_prompt


def test_naturalness_guard_does_not_rewrite_translation_text() -> None:
    translated = "相當理性的人間。"
    issues = detect_unnatural_phrases(translated)
    assert translated == "相當理性的人間。"
    assert issues[0]["phrase"] == "人間"


if __name__ == "__main__":
    test_naturalness_guard_is_retry_worthy_and_feeds_retry_prompt()
    test_naturalness_guard_does_not_rewrite_translation_text()
    print("PASS")
