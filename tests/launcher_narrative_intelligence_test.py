from pathlib import Path
import json

from core.narrative.narrative_intelligence import NarrativeIntelligenceEngine

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    text = """
초인종이 울린 순간 정태의는 멈칫했다.

손에 쥐고 있던 젓가락에서 콩자반이 떨어져 굴렀다.

소리 없이 부슬거리며 비가 내리는 궂은 하늘과 다를 바 없는 기분이었다.

정태의는 집 안에 역병신을 맞아들이는 기분으로 비켜섰다.

정태의는 복잡한 얼굴로 잠시 남자를 바라보다가 한숨 섞어 말했다.
"""

    engine = NarrativeIntelligenceEngine(ROOT)
    analysis = engine.analyze(text)
    prompt_rules = engine.build_prompt_rules(analysis)

    out = ROOT / "prompt_packages" / "narrative_intelligence_test_package.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "source": text,
                "analysis": analysis,
                "prompt_rules": prompt_rules,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    checks = {
        "Literary": len(analysis.get("literary", {}).get("matched_rules", [])) >= 5,
        "Emotion": bool(analysis.get("emotion")),
        "Pacing": bool(analysis.get("pacing")),
        "Inner Monologue": bool(analysis.get("inner_monologue")),
        "Dialogue Beat": bool(analysis.get("dialogue_beat")),
        "Scene Flow": bool(analysis.get("scene_flow")),
        "Prompt Rules": len(prompt_rules) >= 8,
    }

    print("NTPE TQF-06.4.2 Narrative Intelligence Test")
    print("===========================================")

    for name, ok in checks.items():
        print(f"{name:<18} {'PASS' if ok else 'FAIL'}")

    print(f"prompt_rules: {len(prompt_rules)}")
    print(f"package: {out}")

    if not all(checks.values()):
        print("FAIL")
        raise SystemExit(2)

    print("PASS")