from __future__ import annotations

from dataclasses import FrozenInstanceError
import hashlib
import json
import os
from pathlib import Path

from core.literary import LiteraryPromptBuilder, LiteraryTranslationPolicy, normalize_profile, profile_guidance
from core.literary.prompt_profiler import estimate_tokens
from core.prompt_compiler.compiler import PromptCompiler
from core.prompt_compiler.model import PromptSections
from core.translation_discipline import TranslationDisciplineEngine
from core.translation_naturalness import (
    ISSUE_DISCIPLINE_MAPPING,
    NATURALNESS_FREEZE_VERSION,
    NATURALNESS_FROZEN_STAGES,
    TranslationNaturalnessFreeze,
    analyze_unsupported_details,
    analyze_voice_register,
    apply_literary_collocation_guard,
    build_translation_naturalness_freeze,
    canonicalize_novel_chinese,
    render_naturalness_policy,
)
from core.translation_quality_v5.unified_quality_gate import run_unified_quality_gate


def _sections() -> PromptSections:
    return PromptSections("system", "policy", "context", "glossary", "【Korean】\nsource", "【Output】")


def main() -> int:
    root = Path(__file__).resolve().parent
    checks: list[tuple[str, bool]] = []
    freeze = build_translation_naturalness_freeze()
    checks.append(("Freeze implementation exists", (root / "core/translation_naturalness/freeze.py").exists()))
    checks.append(("Freeze API exported", isinstance(freeze, TranslationNaturalnessFreeze)))
    checks.append(("All Naturalness stages frozen", freeze.version == NATURALNESS_FREEZE_VERSION and freeze.frozen_stages == NATURALNESS_FROZEN_STAGES == ("12.1", "12.2", "12.3", "12.4", "12.4.1")))
    try:
        freeze.version = "changed"  # type: ignore[misc]
        immutable = False
    except (FrozenInstanceError, AttributeError, TypeError):
        immutable = True
    try:
        freeze.metadata["frozen"] = False  # type: ignore[index]
        immutable = False
    except TypeError:
        pass
    checks.append(("Freeze object and metadata immutable", immutable))

    previous = os.environ.get("NTPE_NATURALNESS_POLICY")
    try:
        os.environ["NTPE_NATURALNESS_POLICY"] = "1"
        enabled = PromptCompiler(discipline_enabled=False).compile(_sections())
        enabled_profile = LiteraryPromptBuilder().build(chunk_text="그는 말했다.", locked_dictionary={}).prompt_profile
        os.environ["NTPE_NATURALNESS_POLICY"] = "0"
        disabled = PromptCompiler(discipline_enabled=False).compile(_sections())
        disabled_profile = LiteraryPromptBuilder().build(chunk_text="그는 말했다.", locked_dictionary={}).prompt_profile
    finally:
        if previous is None:
            os.environ.pop("NTPE_NATURALNESS_POLICY", None)
        else:
            os.environ["NTPE_NATURALNESS_POLICY"] = previous
    block = render_naturalness_policy()
    base_policy = LiteraryTranslationPolicy().render() + "\n【Profile】\n- " + profile_guidance(normalize_profile("literary"))
    expected_token_delta = estimate_tokens(base_policy + "\n" + block) - estimate_tokens(base_policy)
    checks.append(("Prompt rollback complete", block in enabled.user_prompt and block not in disabled.user_prompt))
    checks.append(("Naturalness policy injected once", enabled.user_prompt.count("【小說語感規範】") == 1))
    checks.append(("Prompt token delta accounted", enabled_profile.policy_tokens - disabled_profile.policy_tokens == expected_token_delta and enabled_profile.total_tokens - disabled_profile.total_tokens == expected_token_delta and enabled_profile.total_chars - disabled_profile.total_chars == len(block) + 1))

    canonical = canonicalize_novel_chinese("普通的觀光客人穿著膝蓋的短褲。。")
    ambiguous = canonicalize_novel_chinese("他嘔了一口氣。")
    checks.append(("Canonicalization remains deterministic", canonical.text == "普通觀光客穿著及膝短褲。"))
    checks.append(("Ambiguous wording is not rewritten", ambiguous.text == "他嘔了一口氣。" and bool(ambiguous.warnings)))
    unsupported = analyze_unsupported_details("그 섬은 멀리 있었다.", "只能搭乘小型飛機前往拉古恩島，路程足足四天。")
    supported = analyze_unsupported_details("소형 비행기로 라군 섬에 갔다. 나흘 걸렸다.", "搭乘小型飛機前往拉古恩島，路程四天。")
    checks.append(("High-confidence unsupported detail blocks", unsupported.blocking))
    checks.append(("Supported concrete details do not misfire", not supported.issues))
    risky = apply_literary_collocation_guard("他嘔了一口氣。")
    checks.append(("Collocation guard avoids semantic rewrite", risky.text == "他嘔了一口氣。"))

    voice_samples = (
        analyze_voice_register("민수는 말했다.", "敏洙：『您請坐。』\n敏洙：『你快走。』"),
        analyze_voice_register("그는 말했다.", "他勃然大怒地咆哮。"),
        analyze_voice_register("그는 말했다.", "他說這消息超扯。", profile="historical_literary"),
    )
    voice_issues = [issue for result in voice_samples for issue in result.issues]
    checks.append(("Voice findings remain nonblocking", all(not result.blocking for result in voice_samples)))
    checks.append(("Voice findings never request retry", all(not issue.to_dict()["retry_required"] for issue in voice_issues)))
    checks.append(("Voice findings never locally repair", all(not issue.locally_repairable and not issue.to_dict()["repairable"] for issue in voice_issues)))
    engine = TranslationDisciplineEngine(profile="literary")
    mappings = {code: getattr(engine.feedback.map_issue_code(code), "code", None) for code in ISSUE_DISCIPLINE_MAPPING}
    checks.append(("Specific Stage 12.4.1 mappings frozen", mappings == ISSUE_DISCIPLINE_MAPPING and "PRESERVE_PARAGRAPH_INTENT" not in mappings.values()))
    checks.append(("Generation rule count remains frozen", len(engine.generation_rules()) == 8 and engine.metadata()["active_rule_count"] == 8))

    quality = {"accepted": True, "retry_required": False, "issues": []}
    legacy = {"enabled": True, "passed": True, "issues": []}
    before = run_unified_quality_gate(quality, legacy)
    analyze_voice_register("그는 말했다.", "他勃然大怒地咆哮。")
    after = run_unified_quality_gate(quality, legacy)
    checks.append(("Quality score and decision unchanged", (before["score"], before["decision"]) == (after["score"], after["decision"])))

    manifest_path = root / "manifests/te_v600_stage125_translation_naturalness_freeze_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    integrity = manifest.get("integrity", {}).get("sha256", {})
    hashes_ok = bool(integrity) and all(hashlib.sha256((root / path).read_bytes()).hexdigest() == digest for path, digest in integrity.items())
    checks.append(("Manifest integrity hashes valid", hashes_ok))
    source = (root / "core/translation_naturalness/freeze.py").read_text(encoding="utf-8")
    checks.append(("No Provider client HTTP or NVIDIA call", all(token not in source for token in ("import requests", "requests.", "urllib", "http://", "https://", "ProviderManager", "TranslationEngine(", "nvidia_api."))))

    width = max(len(name) for name, _ in checks)
    failed = False
    print("TE v6.0 Stage 12.5 Translation Naturalness Engine Freeze")
    for name, passed in checks:
        print(f"{name:<{width}}  {'PASS' if passed else 'FAIL'}")
        failed |= not passed
    print("ALL PASS" if not failed else "FAIL")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
