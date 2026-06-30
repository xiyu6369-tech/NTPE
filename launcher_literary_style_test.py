from pathlib import Path
import json

from core.narrative.literary_style import LiteraryStyleRulesEngine

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    text = """
초인종이 울린 순간 정태의는 멈칫했다.

손에 쥐고 있던 젓가락에서 콩자반이 떨어져 굴렀다.

소리 없이 부슬거리며 비가 내리는 궂은 하늘과 다를 바 없는 기분이었다.

정태의는 집 안에 역병신을 맞아들이는 기분으로 비켜섰다.

정태의는 복잡한 얼굴로 잠시 남자를 바라보다가 한숨 섞어 말했다.
"""

    engine = LiteraryStyleRulesEngine(ROOT)
    analysis = engine.analyze(text)
    prompt_rules = engine.build_prompt_rules(analysis)

    matched_ids = [
        item.get("id")
        for item in analysis.get("matched_rules", [])
    ]

    out = ROOT / "prompt_packages" / "literary_style_test_package.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "source": text,
                "matched_rules": analysis.get("matched_rules", []),
                "prompt_rules": prompt_rules,
                "principles": analysis.get("principles", []),
                "rewrite_preferences": analysis.get("rewrite_preferences", []),
                "forbidden": analysis.get("forbidden", []),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    required = {
        "LIT_PSYCHOLOGY",
        "LIT_ACTION_SEQUENCE",
        "LIT_ATMOSPHERE",
        "LIT_METAPHOR",
        "LIT_DIALOGUE_BEAT",
    }

    print("NTPE TQF-06.4 Literary Style Test")
    print("=================================")
    print(f"Matched Rules: {len(matched_ids)}")

    for rule_id in matched_ids:
        print(f"✓ {rule_id}")

    print(f"Narrative Prompt Rules: {len(prompt_rules)}")
    print(f"package: {out}")

    if not required.issubset(set(matched_ids)):
        print("FAIL")
        raise SystemExit(2)

    print("PASS")