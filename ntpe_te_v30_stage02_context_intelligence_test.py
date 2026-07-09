from __future__ import annotations

from pathlib import Path

from core.translation_engine.context_intelligence import (
    CONTEXT_INTELLIGENCE_MARKER,
    apply_context_intelligence,
    build_context_directives,
    build_context_snapshot,
    detect_context_profile,
    detect_naturalness_warnings,
)
from lts.txt_translation_runtime import TxtTranslationOptions, build_prompt_package


def _base_package(source_text: str) -> dict:
    return {
        "package_id": "v30-stage02-test",
        "model_profile": {"model": "test-model"},
        "prompt": {"system_prompt": "translate", "user_prompt": "source follows"},
        "source": {"chunk_text": source_text, "char_count": len(source_text)},
        "context": {"previous_chunk_tail": "鄭泰義剛推開門，房間裡一片沉默。"},
        "session": {"file_name": "sample.txt", "chunk_index": 2},
    }


def test_detect_context_profile() -> None:
    assert detect_context_profile('"Are you leaving?"\n"No."\n"Then stay."') == "dialogue_heavy"
    assert detect_context_profile("Moonlight filled the quiet room and shadows moved along the corridor.") == "descriptive"
    assert detect_context_profile("His breath shook. Blood darkened his sleeve and panic rose again.") == "tension"
    assert detect_context_profile("A long paragraph continues the scene with steady narration.\nAnother long paragraph follows the same viewpoint.\nA third paragraph keeps explaining the situation.") == "narration_heavy"
    assert detect_context_profile("He went inside.") == "neutral"


def test_build_context_snapshot_contains_continuity() -> None:
    snapshot = build_context_snapshot(
        "鄭泰義站在門口，房間裡很安靜。",
        "他倒抽一口氣，看見牆上的影子。",
        metadata={"chunk": 2},
    )
    assert snapshot["version"] == "3.0-stage02"
    assert snapshot["profile"] in {"descriptive", "tension", "neutral"}
    assert snapshot["narrative_state"] == "continuing_scene"
    assert "鄭泰義" in snapshot["previous_key_info"]
    assert snapshot["metadata"]["chunk"] == 2


def test_context_directives_target_natural_chinese_and_repetition() -> None:
    snapshot = build_context_snapshot("", "可以用十個手指頭就能數得過來。", metadata=None)
    directives = build_context_directives(snapshot)
    joined = "\n".join(directives)
    assert "do not translate word-by-word" in joined
    assert "natural Traditional Chinese novel prose" in joined
    assert "Avoid mechanical repeated structures" in joined
    assert "幾乎十根手指就數得完" in joined


def test_naturalness_guard_warns_without_rewriting() -> None:
    text = "他是相當理性的人間，卻嘔了一口氣。"
    warnings = detect_naturalness_warnings(text)
    assert {item["phrase"] for item in warnings} == {"人間", "嘔了一口氣"}
    package = apply_context_intelligence(_base_package(text), text)
    assert package["source"]["chunk_text"] == text
    assert len(package["qa_warnings"]) == 2
    assert CONTEXT_INTELLIGENCE_MARKER in package["prompt"]["user_prompt"]


def test_apply_context_intelligence_is_idempotent() -> None:
    package = apply_context_intelligence(_base_package("可以用十個手指頭就能數得過來。"), "可以用十個手指頭就能數得過來。")
    enhanced = apply_context_intelligence(package, "可以用十個手指頭就能數得過來。")
    assert enhanced["prompt"]["user_prompt"].count(CONTEXT_INTELLIGENCE_MARKER) == 1
    assert len(enhanced["qa_warnings"]) == 1


def test_txt_runtime_builds_stage02_context_package() -> None:
    options = TxtTranslationOptions(input_path=Path("sample.txt"), output_dir=Path("output"), dry_run=True)
    package = build_prompt_package(
        options=options,
        chunk_text="可以用十個手指頭就能數得過來。",
        chunk_index=2,
        chunk_total=3,
        locked_dictionary={},
        previous_context="鄭泰義剛才停在門口。",
    )
    assert package["metadata"]["context_intelligence"]["version"] == "3.0-stage02"
    assert package["prompt"]["context_snapshot"]["narrative_state"] == "continuing_scene"
    assert package["prompt"]["context_directives"]
    assert package["qa_warnings"][0]["code"] == "NATURALNESS_GUARD"


if __name__ == "__main__":
    test_detect_context_profile()
    test_build_context_snapshot_contains_continuity()
    test_context_directives_target_natural_chinese_and_repetition()
    test_naturalness_guard_warns_without_rewriting()
    test_apply_context_intelligence_is_idempotent()
    test_txt_runtime_builds_stage02_context_package()
    print("NTPE TE-v3.0 Stage-02 Context Intelligence PASS")
