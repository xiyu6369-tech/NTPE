from __future__ import annotations

import os

from core.literary import LiteraryPromptBuilder
from core.prompt_compiler import PromptCompiler, PromptSections, foundation_rule_codes


def main() -> int:
    sections = PromptSections(
        system="SYS", policy="POLICY", context="CONTEXT", glossary="GLOSSARY",
        source="【Korean】\nSOURCE", output="OUTPUT",
    )
    compiled = PromptCompiler(discipline_enabled=True).compile(sections)
    assert compiled.metadata["discipline_enabled"] is True
    assert compiled.metadata["discipline_rule_count"] == len(foundation_rule_codes())
    assert "【翻譯紀律】" in compiled.user_prompt
    assert "不得重述前文" in compiled.user_prompt
    assert "不得新增原文不存在" in compiled.user_prompt
    assert "不得自行補充原文未表達的人物心理" in compiled.user_prompt
    assert "不得摘要" in compiled.user_prompt
    assert compiled.user_prompt.index("【翻譯紀律】") < compiled.user_prompt.index("【Korean】")

    builder = LiteraryPromptBuilder()
    result = builder.build(
        chunk_text="그는 조용히 고개를 끄덕였다.",
        locked_dictionary={}, previous_context="前一段已完成內容", profile="literary",
    )
    assert result.prompt_compiler["discipline_enabled"] is True
    assert "【Previous】前一段已完成內容" in result.user_prompt
    assert "只供承接語境，不得翻譯或改寫進輸出" in result.user_prompt

    old = os.environ.get("NTPE_PROMPT_DISCIPLINE")
    try:
        os.environ["NTPE_PROMPT_DISCIPLINE"] = "0"
        disabled = builder.build(
            chunk_text="그는 조용히 고개를 끄덕였다.",
            locked_dictionary={}, previous_context="", profile="literary",
        )
        assert disabled.prompt_compiler["discipline_enabled"] is False
        assert "【翻譯紀律】" not in disabled.user_prompt
    finally:
        if old is None:
            os.environ.pop("NTPE_PROMPT_DISCIPLINE", None)
        else:
            os.environ["NTPE_PROMPT_DISCIPLINE"] = old

    print("TE v5.5.2 Prompt Discipline")
    print("============================")
    print("Discipline rules injected before source PASS")
    print("No-restatement/addition constraints     PASS")
    print("Previous context protected              PASS")
    print("Immediate rollback switch               PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
