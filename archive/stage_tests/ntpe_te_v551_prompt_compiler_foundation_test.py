from __future__ import annotations

import json
import os
from pathlib import Path

from core.literary import LiteraryPromptBuilder, profile_guidance
from core.prompt_compiler import PROMPT_COMPILER_VERSION, PromptCompiler, PromptSections, foundation_rule_codes


ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "tests" / "literary" / "Prompt_Discipline_Set"


def main() -> int:
    sections = PromptSections(
        system="SYS",
        policy="POLICY",
        context="CONTEXT",
        glossary="GLOSSARY",
        source="SOURCE",
        output="OUTPUT",
    )
    compiled = PromptCompiler().compile(sections)
    assert compiled.system_prompt == "SYS"
    assert compiled.user_prompt == "POLICY\nCONTEXT\nGLOSSARY\nSOURCE\nOUTPUT"
    assert compiled.compiler_version == PROMPT_COMPILER_VERSION
    assert compiled.metadata["discipline_enabled"] is False

    builder = LiteraryPromptBuilder()
    old_discipline = os.environ.get("NTPE_PROMPT_DISCIPLINE")
    os.environ["NTPE_PROMPT_DISCIPLINE"] = "0"
    try:
        result = builder.build(
            chunk_text="그는 조용히 고개를 끄덕였다.",
            locked_dictionary={},
            previous_context="",
            profile="literary",
        )
    finally:
        if old_discipline is None:
            os.environ.pop("NTPE_PROMPT_DISCIPLINE", None)
        else:
            os.environ["NTPE_PROMPT_DISCIPLINE"] = old_discipline
    expected = "\n".join([
        builder.policy.render() + "\n【Profile】\n- " + profile_guidance("literary"),
        "\n".join([result.narrative_context.render(), result.character_context.render()]),
        result.glossary_context.render(),
        "【Korean】\n그는 조용히 고개를 끄덕였다.",
        "【Output】直出譯文，禁止標題、註解、Markdown。",
    ])
    assert result.user_prompt == expected
    assert result.prompt_compiler["mode"] == "legacy_equivalent"

    registered = set(foundation_rule_codes())
    fixture_count = 0
    for path in sorted(FIXTURES.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        required = set(payload.get("required_future_rules", []))
        assert required <= registered, (path.name, required - registered)
        fixture_count += 1
    assert fixture_count >= 4

    print("TE v5.5.1 Prompt Compiler Foundation")
    print("====================================")
    print("Structured compiler output equivalent PASS")
    print("Literary builder text equivalent      PASS")
    print("Discipline disabled in foundation     PASS")
    print("Offline discipline fixtures covered  PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
