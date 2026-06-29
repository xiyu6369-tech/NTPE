from pathlib import Path

from core.prompt_builder.prompt_builder import PromptBuilder

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    text = """패션 1

초인종이 울린 순간 정태의는 멈칫했다.

손에 쥐고 있던 젓가락에서 콩자반이 떨어져 굴렀다.

소리 없이 부슬거리며 비가 내리는 궂은 하늘과 다를 바 없는 기분이었다.

그럼에도 불구하고, 정태의는 집 안에 역병신을 맞아들이는 기분으로 비켜섰다.
"""

    builder = PromptBuilder(root=ROOT)
    package = builder.build(
        chunk_text=text,
        file_name="style_planner_test.txt",
        chunk_index=1,
        chunk_total=1,
        session_id="STYLE_PLANNER_TEST",
    )

    out = ROOT / "prompt_packages" / "style_planner_test_package.json"
    builder.save_package(package, out)

    plan = package["style_profile"].get("novel_style_plan", {})
    matched = plan.get("matched_rules", [])

    print("NTPE TQF-05.1 Novel Style Planner")
    print("=================================")
    print(f"style_target: {plan.get('style_target', '')}")
    print(f"matched_rules: {len(matched)}")
    for item in matched:
        print(f"- {item.get('id')}: {item.get('instruction')}")
    print(f"package: {out}")

    if len(matched) < 2:
        print("FAIL")
        raise SystemExit(2)

    print("PASS")
