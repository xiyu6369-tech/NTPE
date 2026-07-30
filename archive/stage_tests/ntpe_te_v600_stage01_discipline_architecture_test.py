from __future__ import annotations

import os
from pathlib import Path

from core.prompt_compiler import PromptCompiler, PromptSections, foundation_rule_codes
from core.translation_discipline import (
    AdaptiveFeedbackAdapter,
    DisciplineRuleRegistry,
    PromptCompilerAdapter,
    TranslationDisciplineEngine,
    UnifiedQualityGateAdapter,
    legacy_prompt_discipline_rules,
    normalize_discipline_profile,
)
from lts.txt_translation_runtime import TxtTranslationOptions, build_prompt_package


def main() -> int:
    assert normalize_discipline_profile("literary") == "literary_balanced"
    rules = legacy_prompt_discipline_rules()
    assert len(rules) == 8
    assert tuple(rule.code for rule in rules) == foundation_rule_codes()
    registry = DisciplineRuleRegistry(rules)
    assert len(registry.all()) == len({rule.code for rule in registry.all()}) == 8

    sections = PromptSections(system="SYS", policy="POLICY", context="CONTEXT", glossary="GLOSSARY", source="SOURCE", output="OUTPUT")
    legacy = PromptCompiler(discipline_enabled=True).compile(sections)
    adapted = PromptCompilerAdapter(PromptCompiler(discipline_enabled=True)).compile(sections)
    assert adapted.system_prompt == legacy.system_prompt
    assert adapted.user_prompt == legacy.user_prompt
    assert adapted.section_order == legacy.section_order

    engine = TranslationDisciplineEngine("literary")
    feedback = AdaptiveFeedbackAdapter(registry)
    assert feedback.map_issue_code("TOO_SHORT").code == "NO_SUMMARIZATION"
    assert feedback.map_issue_code("SEMANTIC_DUPLICATE_PARAGRAPH").code == "NO_PREVIOUS_RESTATEMENT"

    original = {"decision": "retry_required", "score": 42, "merged_issues": [{"code": "TOO_SHORT"}]}
    mapped = UnifiedQualityGateAdapter(feedback).adapt(original)
    assert mapped["decision"] == original["decision"] and mapped["score"] == original["score"]
    assert mapped["discipline_rule_codes"] == ["NO_SUMMARIZATION"]

    metadata = engine.metadata(enabled=True)
    assert metadata["discipline_engine_version"] == "6.0.0"
    assert metadata["discipline_profile"] == "literary_balanced"
    assert metadata["active_rule_count"] == metadata["generation_rule_count"] == 8
    report = engine.report()
    assert report["schema_version"] == "6.0.0-stage01"
    assert len(report["active_rules"]) == 8

    package = build_prompt_package(
        options=TxtTranslationOptions(input_path=Path("stage01.txt"), output_dir=Path("."), quality_profile="literary", dry_run=True),
        chunk_text="source", chunk_index=1, chunk_total=1, locked_dictionary={},
    )
    runtime = package["prompt_runtime"]
    for key in ("prompt_compiler", "prompt_discipline_enabled", "discipline_rule_count", "runtime_wiring_verified"):
        assert key in runtime
    assert runtime["discipline_engine_version"] == "6.0.0"
    assert runtime["discipline_profile"] == "literary_balanced"
    assert runtime["active_rule_count"] == runtime["generation_rule_count"] == 8

    old = os.environ.get("NTPE_PROMPT_DISCIPLINE")
    try:
        os.environ["NTPE_PROMPT_DISCIPLINE"] = "0"
        disabled = TranslationDisciplineEngine().metadata(enabled=False)
        assert disabled["active_rule_codes"] == [] and disabled["active_rule_count"] == 0
    finally:
        if old is None:
            os.environ.pop("NTPE_PROMPT_DISCIPLINE", None)
        else:
            os.environ["NTPE_PROMPT_DISCIPLINE"] = old

    print("TE v6.0 Stage 01 Discipline Architecture")
    print("==========================================")
    print("Legacy rules registered              PASS")
    print("Compiler output equivalent           PASS")
    print("Issue mappings decision-neutral      PASS")
    print("Metadata and rollback compatible     PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
