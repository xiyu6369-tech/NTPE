from __future__ import annotations

import os
from pathlib import Path

from core.prompt_compiler import PromptCompiler, PromptSections
from core.prompt_compiler.rules import render_discipline_block, enabled_discipline_rules
from core.translation_discipline import TranslationDisciplineEngine
from lts.txt_translation_runtime import TxtTranslationOptions, build_prompt_package


def main() -> int:
    engine = TranslationDisciplineEngine("literary")
    canonical = engine.render_generation_policy(enabled=True)
    legacy = render_discipline_block(enabled_discipline_rules())
    assert canonical == legacy
    assert len(engine.generation_rules()) == 8

    sections = PromptSections(
        system="SYS", policy="POLICY", context="CONTEXT", glossary="GLOSSARY",
        source="【Korean】\nSOURCE", output="OUTPUT",
    )
    compiled = PromptCompiler(discipline_enabled=True).compile(sections)
    assert canonical in compiled.user_prompt
    assert compiled.metadata["discipline_policy_version"] == "6.0.0-stage02"
    assert compiled.metadata["discipline_policy_source"] == "core.translation_discipline"
    assert compiled.metadata["discipline_rule_count"] == 8

    package = build_prompt_package(
        options=TxtTranslationOptions(
            input_path=Path("stage02.txt"), output_dir=Path("."),
            quality_profile="literary", dry_run=True,
        ),
        chunk_text="source", chunk_index=1, chunk_total=1, locked_dictionary={},
    )
    runtime = package["prompt_runtime"]
    assert runtime["discipline_policy_version"] == "6.0.0-stage02"
    assert runtime["discipline_policy_source"] == "core.translation_discipline"
    assert runtime["active_rule_count"] == 8
    assert "【翻譯紀律】" in package["prompt"]["user_prompt"]

    adaptive = engine.adaptive_rules(["PARAGRAPH_OMISSION_SUSPECTED", "HALLUCINATION"])
    assert [rule.code for rule in adaptive] == ["PRESERVE_PARAGRAPH_INTENT", "NO_ADDED_PLOT"]

    old = os.environ.get("NTPE_PROMPT_DISCIPLINE")
    try:
        os.environ["NTPE_PROMPT_DISCIPLINE"] = "0"
        disabled = build_prompt_package(
            options=TxtTranslationOptions(
                input_path=Path("stage02-disabled.txt"), output_dir=Path("."),
                quality_profile="literary", dry_run=True,
            ),
            chunk_text="source", chunk_index=1, chunk_total=1, locked_dictionary={},
        )
        assert "【翻譯紀律】" not in disabled["prompt"]["user_prompt"]
        assert disabled["prompt_runtime"]["active_rule_count"] == 0
    finally:
        if old is None:
            os.environ.pop("NTPE_PROMPT_DISCIPLINE", None)
        else:
            os.environ["NTPE_PROMPT_DISCIPLINE"] = old

    print("TE v6.0 Stage 02 Discipline Policy Activation")
    print("===============================================")
    print("Canonical policy text equivalent       PASS")
    print("Prompt Compiler uses unified policy    PASS")
    print("Runtime metadata activated             PASS")
    print("Adaptive issues map to policy rules    PASS")
    print("Rollback remains compatible            PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
