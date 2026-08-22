from pathlib import Path
from core.prompt_builder.prompt_builder import PromptBuilder

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    text = """패션 1

초인종이 울린 순간 정태의는 멈칫했다.

손에 쥐고 있던 젓가락에서 콩자반이 떨어져 굴렀다.

정태의는 현관 쪽으로 신경질적인 시선을 주었다.
"""

    builder = PromptBuilder(root=ROOT)
    package = builder.build(
        chunk_text=text,
        file_name="novel_prompt_test.txt",
        chunk_index=1,
        chunk_total=1,
        session_id="NOVEL_PROMPT_TEST",
    )

    out = ROOT / "prompt_packages" / "novel_prompt_test_package.json"
    builder.save_package(package, out)

    npe = package["style_profile"].get("novel_prompt_engine", {})
    rules = package["rules"].get("novel_prompt_rules", [])

    print("NTPE v1.1 / TQF-06.1 Novel Prompt Engine")
    print("========================================")
    print(f"target: {npe.get('target', '')}")
    print(f"focus_count: {len(npe.get('focus', []))}")
    print(f"novel_prompt_rules: {len(rules)}")
    print(f"package: {out}")

    if len(rules) < 10:
        print("FAIL")
        raise SystemExit(2)

    print("PASS")
