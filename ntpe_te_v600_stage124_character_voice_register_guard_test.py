from __future__ import annotations

import os
from pathlib import Path

from core.prompt_compiler.compiler import PromptCompiler
from core.prompt_compiler.model import PromptSections
from core.translation_discipline import TranslationDisciplineEngine
from core.translation_naturalness import ISSUE_DISCIPLINE_MAPPING, analyze_voice_register


def _sections() -> PromptSections:
    return PromptSections("system", "policy", "context", "glossary", "【Korean】\nsource", "【Output】")


def main() -> int:
    checks: list[tuple[str, bool]] = []
    clean = analyze_voice_register("민수는 정중하게 말했다.", "敏洙：『您好。』\n敏洙：『請您坐。』")
    checks.append(("Consistent adjacent voice is clean", not clean.issues))
    honorific = analyze_voice_register("민수는 말했다.", "敏洙：『您請坐。』\n敏洙：『你快走。』")
    checks.append(("Honorific drift detected", any(x.code == "HONORIFIC_REGISTER_DRIFT" for x in honorific.issues)))
    viewpoint = analyze_voice_register("그는 문을 열었다. 그녀는 기다렸다.", "他打開門。我在房裡等著。")
    checks.append(("Third to first viewpoint drift detected", any(x.code == "NARRATIVE_VIEWPOINT_DRIFT" for x in viewpoint.issues)))
    marked = analyze_voice_register("그는 말했다. 나는 대답했다.", "他說：『我知道。』旁白仍描述他轉身離開。")
    checks.append(("Explicit dialogue and narration not mixed", not any(x.code == "DIALOGUE_NARRATION_REGISTER_MIX" for x in marked.issues)))
    era = analyze_voice_register("그는 소식을 전했다.", "他笑說這消息超扯，還要大家按讚。", profile="historical_literary")
    checks.append(("Modern slang warned in period profile", any(x.code == "ERA_INAPPROPRIATE_EXPRESSION" for x in era.issues)))
    modern = analyze_voice_register("그는 휴대폰으로 방송했다.", "他拿手機直播。", profile="modern_literary")
    checks.append(("Modern terms allowed in modern profile", not any(x.code == "ERA_INAPPROPRIATE_EXPRESSION" for x in modern.issues)))
    emotion = analyze_voice_register("그는 말했다.", "他勃然大怒地咆哮。")
    checks.append(("Unsupported emotional amplification detected", any(x.code == "UNSUPPORTED_EMOTIONAL_AMPLIFICATION" for x in emotion.issues)))
    checks.append(("Issues remain nonblocking", not era.blocking and not emotion.blocking))
    engine = TranslationDisciplineEngine(profile="literary")
    mapped = engine.feedback.map_issue_code("UNSUPPORTED_EMOTIONAL_AMPLIFICATION")
    checks.append(("High-confidence issue maps to Discipline", mapped is not None and mapped.code == ISSUE_DISCIPLINE_MAPPING["UNSUPPORTED_EMOTIONAL_AMPLIFICATION"]))
    checks.append(("No subjective local rewrite", all(not x.locally_repairable for x in honorific.issues + emotion.issues)))
    metadata = emotion.to_metadata()
    checks.append(("Offline fail-closed metadata", not metadata["provider_called"] and metadata["fail_closed"] and not metadata["semantic_rewrite_allowed"]))

    previous = os.environ.get("NTPE_NATURALNESS_POLICY")
    try:
        os.environ["NTPE_NATURALNESS_POLICY"] = "0"
        rollback = PromptCompiler(discipline_enabled=True).compile(_sections())
        checks.append(("Prompt rollback remains effective", "【小說語感規範】" not in rollback.user_prompt))
    finally:
        if previous is None:
            os.environ.pop("NTPE_NATURALNESS_POLICY", None)
        else:
            os.environ["NTPE_NATURALNESS_POLICY"] = previous

    guard_source = Path("core/translation_naturalness/voice_register_guard.py").read_text(encoding="utf-8")
    runtime_source = Path("lts/txt_translation_runtime.py").read_text(encoding="utf-8")
    checks.append(("No Provider client or HTTP", "requests" not in guard_source and "http" not in guard_source.lower()))
    checks.append(("Runtime guard precedes unsupported detail", runtime_source.index("candidate_voice_register =") < runtime_source.index("unsupported_detail_guard =", runtime_source.index("candidate_voice_register ="))))
    checks.append(("Runtime metadata wired", '"voice_register_guard"' in runtime_source))

    width = max(len(name) for name, _ in checks)
    failed = False
    print("TE v6.0 Stage 12.4 Character Voice & Narrative Register Guard")
    for name, passed in checks:
        print(f"{name:<{width}}  {'PASS' if passed else 'FAIL'}")
        failed |= not passed
    print("ALL PASS" if not failed else "FAIL")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
