from __future__ import annotations

from pathlib import Path

from core.translation_engine.prompt_intelligence import (
    PROMPT_INTELLIGENCE_MARKER,
    apply_prompt_intelligence,
    build_quality_directives,
    detect_text_profile,
    enhance_prompt_package,
)
from lts.txt_translation_runtime import TxtTranslationOptions, build_prompt_package


def _base_package(source_text: str) -> dict:
    return {
        "package_id": "v30-stage01-test",
        "model_profile": {"model": "test-model"},
        "prompt": {"system_prompt": "translate", "user_prompt": "source follows"},
        "source": {"chunk_text": source_text, "char_count": len(source_text)},
        "session": {"file_name": "sample.txt", "chunk_index": 1},
    }


def test_detect_text_profile() -> None:
    assert detect_text_profile('"Are you leaving?"\n"No."\n"Then stay."') == "dialogue_heavy"
    assert detect_text_profile("We shall therefore proceed pursuant to the formal request.") == "formal"
    assert detect_text_profile("Moonlight sank into the silent room. Her breath trembled in the night.") == "literary"
    assert detect_text_profile("A long paragraph describes the corridor and the storm outside.\nAnother long paragraph keeps the camera in narration.\nA third line continues the scene without speech.") == "narration_heavy"


def test_build_quality_directives_contains_stage01_rules() -> None:
    directives = build_quality_directives("formal")
    joined = "\n".join(directives)
    assert "Traditional Chinese" in joined
    assert "do not summarize" in joined
    assert "「」" in joined
    assert "Avoid forced Taiwanese colloquial wording" in joined
    assert "formal" in joined


def test_enhance_prompt_package_preserves_old_schema() -> None:
    package = _base_package('"Wait," she said.')
    enhanced = enhance_prompt_package(package)
    assert enhanced is not package
    assert enhanced["package_id"] == package["package_id"]
    assert enhanced["prompt"]["system_prompt"] == "translate"
    assert enhanced["metadata"]["prompt_intelligence"]["version"] == "3.0-stage01"
    assert enhanced["prompt"]["prompt_intelligence"]["profile"] == "dialogue_heavy"
    assert PROMPT_INTELLIGENCE_MARKER in enhanced["prompt"]["user_prompt"]


def test_apply_prompt_intelligence_is_idempotent() -> None:
    package = apply_prompt_intelligence(_base_package('"Stay."'), '"Stay."')
    enhanced = apply_prompt_intelligence(package, '"Stay."')
    assert enhanced["prompt"]["user_prompt"].count(PROMPT_INTELLIGENCE_MARKER) == 1


def test_txt_runtime_builds_v30_prompt_intelligence_package() -> None:
    options = TxtTranslationOptions(input_path=Path("sample.txt"), output_dir=Path("output"), dry_run=True)
    package = build_prompt_package(
        options=options,
        chunk_text='"Are you all right?"\n"I am."',
        chunk_index=1,
        chunk_total=1,
        locked_dictionary={},
    )
    assert package["metadata"]["prompt_intelligence"]["version"] == "3.0-stage01"
    assert package["prompt"]["prompt_intelligence"]["profile"] == "dialogue_heavy"
    assert PROMPT_INTELLIGENCE_MARKER in package["prompt"]["user_prompt"]


if __name__ == "__main__":
    test_detect_text_profile()
    test_build_quality_directives_contains_stage01_rules()
    test_enhance_prompt_package_preserves_old_schema()
    test_apply_prompt_intelligence_is_idempotent()
    test_txt_runtime_builds_v30_prompt_intelligence_package()
    print("NTPE TE-v3.0 Stage-01 Prompt Intelligence PASS")
