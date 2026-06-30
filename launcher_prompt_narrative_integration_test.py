from pathlib import Path

from core.prompt_builder.prompt_builder import PromptBuilder

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    text = """
초인종이 울린 순간 정태의는 멈칫했다.

손에 쥐고 있던 젓가락에서 콩자반이 떨어져 굴렀다.

소리 없이 부슬거리며 비가 내리는 궂은 하늘과 다를 바 없는 기분이었다.

정태의는 집 안에 역병신을 맞아들이는 기분으로 비켜섰다.

정태의는 복잡한 얼굴로 잠시 남자를 바라보다가 한숨 섞어 말했다.
"""

    builder = PromptBuilder(ROOT)
    package = builder.build(
        chunk_text=text,
        file_name="narrative_prompt_test.txt",
        chunk_index=1,
        chunk_total=1,
        session_id="NARRATIVE_PROMPT_TEST",
    )

    out = ROOT / "prompt_packages" / "narrative_prompt_integration_test_package.json"
    builder.save_package(package, out)

    rules = package["rules"].get("novel_prompt_rules", [])
    prompt_text = package["prompt"]["user_prompt"]

    checks = {
        "Narrative Rules": len(rules) >= 26,
        "Psychology": "心理" in prompt_text,
        "Action": "動作" in prompt_text,
        "Atmosphere": "氛圍" in prompt_text or "場景" in prompt_text,
        "Metaphor": "比喻" in prompt_text,
        "Dialogue Beat": "對話" in prompt_text,
    }

    print("NTPE TQF-06.4.3 Narrative Prompt Integration Test")
    print("=================================================")

    for name, ok in checks.items():
        print(f"{name:<18} {'PASS' if ok else 'FAIL'}")

    print(f"package: {out}")

    if not all(checks.values()):
        print("FAIL")
        raise SystemExit(2)

    print("PASS")