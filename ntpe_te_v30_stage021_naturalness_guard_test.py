from __future__ import annotations

from pathlib import Path

from core.translation_engine.context_intelligence import (
    build_naturalness_repair_directives,
    detect_unnatural_phrases,
)
from lts.txt_translation_runtime import (
    TxtTranslationOptions,
    analyze_translation_quality,
    build_qa_retry_user_prompt,
)


def test_detect_unnatural_phrases_catches_high_risk_terms() -> None:
    text = "相當理性的人間。鄭泰義嘔了一口氣。可以用十個手指頭就能數得過來。觀光客人纏繞在一起。"
    issues = detect_unnatural_phrases(text)
    phrases = {issue["phrase"] for issue in issues}
    assert phrases == {
        "人間",
        "嘔了一口氣",
        "可以用十個手指頭就能數得過來",
        "觀光客人",
        "纏繞在一起",
    }
    assert all(issue["risk"] == "high" for issue in issues)


def test_build_naturalness_repair_directives() -> None:
    issues = detect_unnatural_phrases("人間。嘔了一口氣。可以用十個手指頭就能數得過來。")
    directives = build_naturalness_repair_directives(issues)
    joined = "\n".join(directives)
    assert "正常人" in joined
    assert "倒抽一口氣" in joined
    assert "十根手指就數得完" in joined


def test_literary_runtime_qa_retries_high_risk_naturalness() -> None:
    options = TxtTranslationOptions(
        input_path=Path("sample.txt"),
        output_dir=Path("output"),
        quality_profile="literary",
        min_length_ratio=0.0,
        max_korean_chars=0,
    )
    report = analyze_translation_quality(
        "그는 숨을 삼켰다.",
        "鄭泰義嘔了一口氣。",
        options,
        locked_dictionary={},
    )
    issue = next(item for item in report["issues"] if item["code"] == "NATURALNESS_GUARD")
    assert report["passed"] is False
    assert issue["severity"] == "error"
    assert issue["retry_worthy"] is True


def test_non_literary_runtime_qa_warns_only() -> None:
    options = TxtTranslationOptions(
        input_path=Path("sample.txt"),
        output_dir=Path("output"),
        quality_profile="balanced",
        speed="fast",
        min_length_ratio=0.0,
        max_korean_chars=0,
    )
    report = analyze_translation_quality("source", "相當理性的人間。", options, locked_dictionary={})
    issue = next(item for item in report["issues"] if item["code"] == "NATURALNESS_GUARD")
    assert report["passed"] is True
    assert issue["severity"] == "warning"


def test_qa_retry_prompt_includes_naturalness_repair_directive() -> None:
    report = {
        "issues": [
            {
                "code": "NATURALNESS_GUARD",
                "message": "high-risk",
                "samples": detect_unnatural_phrases("鄭泰義嘔了一口氣。"),
                "severity": "error",
            }
        ]
    }
    retry_prompt = build_qa_retry_user_prompt("Translate fully.", report, 2)
    assert "Naturalness Guard repair directives" in retry_prompt
    assert "倒抽一口氣" in retry_prompt
    assert "悶哼一聲" in retry_prompt


if __name__ == "__main__":
    test_detect_unnatural_phrases_catches_high_risk_terms()
    test_build_naturalness_repair_directives()
    test_literary_runtime_qa_retries_high_risk_naturalness()
    test_non_literary_runtime_qa_warns_only()
    test_qa_retry_prompt_includes_naturalness_repair_directive()
    print("NTPE TE-v3.0 Stage-02.1 Naturalness Guard PASS")
