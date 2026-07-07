from core.literary import LiteraryPromptBuilder


def main() -> int:
    text = "정태의는 난감해하고 있었다. 그러나 카일이 주장하며 정태의만 데리고 섬으로 왔다."
    locked = {"정태의": "鄭泰義", "카일": "凱爾"}
    result = LiteraryPromptBuilder().build(
        chunk_text=text,
        locked_dictionary=locked,
        alias_map={"定泰義": "鄭泰義"},
        previous_context="",
        profile="literary",
    )
    checks = [
        ("System Prompt", "文學級韓文小說翻譯引擎" in result.system_prompt),
        ("Narrative Context", "난감하다" in result.user_prompt and "為難" in result.user_prompt),
        ("Character Context", "鄭泰義" in result.user_prompt and "凱爾" in result.user_prompt),
        ("Subject Hint", "카일이 주장" in result.user_prompt or "凱爾" in "\n".join(result.character_context.subject_hints)),
        ("Glossary Lock", "정태의 → 鄭泰義" in result.user_prompt),
        ("Alias Lock", "定泰義" in result.user_prompt),
        ("Prompt Mode", result.to_prompt_dict()["prompt_mode"] == "literary_narrative_understanding_ps04"),
    ]
    print("NTPE PS-04 Narrative & Character Understanding Test")
    print("=====================================================")
    failed = False
    for name, ok in checks:
        print(f"{name:<20} {'PASS' if ok else 'FAIL'}")
        failed = failed or not ok
    print("PASS" if not failed else "FAIL")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
