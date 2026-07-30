from __future__ import annotations

from pathlib import Path

from core.translation_discipline import TranslationDisciplineEngine
from core.translation_naturalness import ISSUE_DISCIPLINE_MAPPING, analyze_voice_register
from core.translation_quality_v5.unified_quality_gate import run_unified_quality_gate


EXPECTED = {
    "CHARACTER_VOICE_DRIFT": "CHARACTER_VOICE_CONSISTENCY",
    "HONORIFIC_REGISTER_DRIFT": "HONORIFIC_REGISTER_CONSISTENCY",
    "RELATIONSHIP_DISTANCE_DRIFT": "RELATIONSHIP_DISTANCE_CONSISTENCY",
    "NARRATIVE_VIEWPOINT_DRIFT": "NARRATIVE_VIEWPOINT_CONSISTENCY",
    "NARRATIVE_REGISTER_DRIFT": "NARRATIVE_REGISTER_CONSISTENCY",
    "ERA_INAPPROPRIATE_EXPRESSION": "ERA_REGISTER_CONSISTENCY",
    "DIALOGUE_NARRATION_REGISTER_MIX": "DIALOGUE_NARRATION_SEPARATION",
    "UNSUPPORTED_EMOTIONAL_AMPLIFICATION": "NO_ADDED_PSYCHOLOGY",
}


def main() -> int:
    checks: list[tuple[str, bool]] = []
    engine = TranslationDisciplineEngine(profile="literary")
    actual = {code: getattr(engine.feedback.map_issue_code(code), "code", None) for code in EXPECTED}
    checks.append(("All eight issue mappings are exact", actual == EXPECTED == ISSUE_DISCIPLINE_MAPPING))
    codes = [rule.code for rule in engine.registry.all()]
    checks.append(("Registry rule codes are unique", len(codes) == len(set(codes))))
    checks.append(("No voice issue maps to paragraph intent", all(value != "PRESERVE_PARAGRAPH_INTENT" for value in actual.values())))
    checks.append(("Seven specific rules are registered", all(code in codes for code in set(EXPECTED.values()) - {"NO_ADDED_PSYCHOLOGY"})))

    guard = analyze_voice_register("그는 말했다.", "他勃然大怒地咆哮。")
    issue = guard.issues[0].to_dict()
    checks.append(("Guard remains nonblocking", not guard.blocking and not issue["retry_required"]))
    checks.append(("Guard remains non-repairing", not issue["locally_repairable"] and not issue["repairable"]))
    checks.append(("Guard remains offline", not guard.provider_called and guard.fail_closed))

    quality = {"accepted": True, "retry_required": False, "issues": []}
    legacy = {"enabled": True, "passed": True, "issues": []}
    before = run_unified_quality_gate(quality, legacy)
    analyze_voice_register("그는 말했다.", "他勃然大怒地咆哮。")
    after = run_unified_quality_gate(quality, legacy)
    checks.append(("Quality score is unchanged", before["score"] == after["score"]))
    checks.append(("Unified decision is unchanged", before["decision"] == after["decision"]))

    guard_source = Path("core/translation_naturalness/voice_register_guard.py").read_text(encoding="utf-8")
    runtime_source = Path("lts/txt_translation_runtime.py").read_text(encoding="utf-8")
    checks.append(("No Provider or HTTP implementation", all(token not in guard_source for token in ("requests", "http://", "https://", "ProviderManager", "TranslationEngine("))))
    checks.append(("Runtime keeps evidence outside score issues", 'metrics", {})["voice_register_guard"]' in runtime_source and "extend(\n                            issue.to_dict() for issue in candidate_voice_register.issues" not in runtime_source))

    width = max(len(name) for name, _ in checks)
    failed = False
    print("TE v6.0 Stage 12.4.1 Voice/Register Discipline Mapping Refinement")
    for name, passed in checks:
        print(f"{name:<{width}}  {'PASS' if passed else 'FAIL'}")
        failed |= not passed
    print("ALL PASS" if not failed else "FAIL")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
