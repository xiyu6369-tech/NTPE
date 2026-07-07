import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lts.txt_translation_runtime import TxtTranslationOptions, build_prompt_package


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    options = TxtTranslationOptions(input_path=root / "tests" / "literary" / "Golden_Set" / "original_ko.txt", output_dir=root / "output", quality_profile="literary")
    package = build_prompt_package(
        options=options,
        chunk_text="정태의는 난감해하고 있었다. 카일이 주장하며 휴가를 왔다.",
        chunk_index=1,
        chunk_total=1,
        locked_dictionary={"정태의": "鄭泰義", "카일": "凱爾"},
        previous_context="",
    )
    prompt = package["prompt"]
    context = package["context"]
    checks = [
        ("Package Version", package["metadata"]["package_version"] == "1.2-ps-04-narrative-character-understanding"),
        ("Prompt Mode", prompt["prompt_mode"] == "literary_narrative_understanding_ps04"),
        ("Narrative Context", "narrative_context" in context),
        ("Character Context", "character_context" in context),
        ("Subject Guidance", "主詞" in prompt["user_prompt"] or "Subject" in prompt["user_prompt"]),
        ("Locked Names", "정태의 → 鄭泰義" in prompt["user_prompt"] and "카일 → 凱爾" in prompt["user_prompt"]),
    ]
    print("NTPE PS-04 Integration Test")
    print("===========================")
    failed = False
    for name, ok in checks:
        print(f"{name:<20} {'PASS' if ok else 'FAIL'}")
        failed = failed or not ok
    print("PASS" if not failed else "FAIL")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
