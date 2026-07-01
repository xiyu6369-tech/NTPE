import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.intelligence import TranslationIntelligenceEngine


def check(name, condition):
    status = "PASS" if condition else "FAIL"
    print(f"{name:<32} {status}")
    if not condition:
        raise AssertionError(name)


def main():
    print("NTPE Foundation-07.1 Translation Intelligence Engine Test")
    print("=" * 62)

    engine = TranslationIntelligenceEngine()

    character = engine.characters.remember(
        "정태의",
        "鄭泰義",
        aliases=["태의"],
        traits=["陽光", "適應力強"],
        notes="主要角色",
    )
    check("Character Engine", character.target_name == "鄭泰義")
    check("Character Resolve", engine.characters.resolve("태의").target_name == "鄭泰義")

    glossary = engine.glossary.remember(
        "일라이 리그로우",
        "伊萊・里格勞",
        category="character",
        locked=True,
    )
    check("Glossary Engine", glossary.target_term == "伊萊・里格勞")
    check("Glossary Fuzzy Resolve", engine.glossary.resolve("일라이 리그로", fuzzy=True).target_term == "伊萊・里格勞")

    narrative = engine.narrative.remember(
        "relationship:태의:일라이",
        "兩人關係緊張且具有強烈牽引力",
        scope="volume-1",
        weight=5,
    )
    check("Narrative Engine", narrative.weight == 5)
    check("Narrative Ranked", engine.narrative.ranked(scope="volume-1")[0]["key"] == "relationship:태의:일라이")

    scene = engine.scenes.remember(
        "scene-001",
        "鄭泰義與伊萊在走廊交會",
        location="走廊",
        timeline="夜晚",
        participants=["鄭泰義", "伊萊・里格勞"],
    )
    check("Scene Engine", scene.location == "走廊")
    check("Scene Current", engine.scenes.current().scene_id == "scene-001")

    source_text = "정태의는 일라이 리그로우를 보았다."
    output_text = "鄭泰義看見了伊萊・里格勞。"
    processed = engine.process_segment(source_text, output_text, segment_id="seg-001")
    check("Process Segment", processed["segment_id"] == "seg-001")
    check("Prompt Context", processed["prompt_context"]["type"] == "translation_intelligence_engine_context")
    check("Consistency Engine", processed["consistency"]["passed"] is True)

    bad = engine.consistency.validate_translation(source_text, "他看見了那個男人。")
    check("Consistency Issues", bad["issue_count"] >= 2)

    manifest = engine.attach_to_manifest({"components": []})
    check("Runtime Manifest", manifest["components"][-1]["name"] == "translation_intelligence_engine")

    prompt_package = engine.attach_to_prompt_package({"context_components": []}, source_text=source_text)
    check("Prompt Package", prompt_package["context_components"][-1]["version"] == "foundation-07.1")

    snapshot = engine.build_snapshot()
    check("Snapshot Manifest", snapshot["manifest"]["foundation"] == "07.1")
    check("Backward Store", snapshot["manifest"]["character_count"] == 1)

    print("PASS")


if __name__ == "__main__":
    main()
