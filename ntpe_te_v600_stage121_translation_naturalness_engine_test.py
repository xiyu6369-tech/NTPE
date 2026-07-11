from __future__ import annotations

import os

from core.prompt_compiler.compiler import PromptCompiler
from core.prompt_compiler.model import PromptSections
from core.translation_naturalness import (
    NATURALNESS_RULES,
    canonicalize_novel_chinese,
    render_naturalness_policy,
)


def _sections() -> PromptSections:
    return PromptSections(
        system="system",
        policy="policy",
        context="context",
        glossary="glossary",
        source="【Korean】\nsource",
        output="【Output】",
    )


def main() -> None:
    block = render_naturalness_policy()
    assert "【小說語感規範】" in block
    assert len(NATURALNESS_RULES) == 4
    print("Naturalness policy registered             PASS")

    previous = os.environ.get("NTPE_NATURALNESS_POLICY")
    try:
        os.environ["NTPE_NATURALNESS_POLICY"] = "1"
        compiled = PromptCompiler(discipline_enabled=True).compile(_sections())
        assert "【小說語感規範】" in compiled.user_prompt
        assert compiled.metadata["naturalness_rule_count"] == 4

        os.environ["NTPE_NATURALNESS_POLICY"] = "0"
        rollback = PromptCompiler(discipline_enabled=True).compile(_sections())
        assert "【小說語感規範】" not in rollback.user_prompt
    finally:
        if previous is None:
            os.environ.pop("NTPE_NATURALNESS_POLICY", None)
        else:
            os.environ["NTPE_NATURALNESS_POLICY"] = previous
    print("Prompt policy and rollback switch        PASS")

    result = canonicalize_novel_chinese("普通的觀光客人穿著膝蓋的短褲，旁邊站著秘書般的人物。")
    assert result.text == "普通觀光客穿著及膝短褲，旁邊站著秘書模樣的人。"
    assert result.changed
    print("Safe deterministic canonicalization      PASS")

    warning = canonicalize_novel_chinese("鄭泰義嘔了一口氣。")
    assert warning.text == "鄭泰義嘔了一口氣。"
    assert warning.warnings and not warning.changed
    print("Ambiguous wording remains fail-closed    PASS")
    print("ALL PASS")


if __name__ == "__main__":
    main()
