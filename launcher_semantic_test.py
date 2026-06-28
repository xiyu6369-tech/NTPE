from pathlib import Path
import json

from core.prompt_builder.prompt_builder import PromptBuilder

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    text = """패션 1

초인종이 울린 순간 정태의는 멈칫했다.

소리 없이 부슬거리며 비가 내리는 궂은 하늘과 다를 바 없는 기분으로 간단한 아침 식사를 늘어 놓고 두어 술 떴을 때였다.

뚜걱, 발소리도 한 번 더 울린다. 각지고 무거운 소리다. 군화 소리와 닮았다.

지은 지 20년도 더 된 낡아빠진 연립주택은, 건물에 고양이 한마리라도 들어오면 그 소리가 옥탑층까지 울려 금세 알 수 있었다.

그럼에도 불구하고, 정태의는 집 안에 역병신을 맞아들이는 기분으로 비켜섰다.
"""

    builder = PromptBuilder(root=ROOT)
    package = builder.build(
        chunk_text=text,
        file_name="semantic_test.txt",
        chunk_index=1,
        chunk_total=1,
        session_id="SEMANTIC_TEST",
    )

    out = ROOT / "prompt_packages" / "semantic_test_package.json"
    builder.save_package(package, out)

    matches = package["knowledge"].get("semantic_matches", [])
    dictionary = package["knowledge"].get("semantic_dictionary", {})

    print("NTPE TQF-02 Semantic Translation Engine")
    print("=======================================")
    print(f"semantic_matches: {len(matches)}")
    for item in matches:
        print(f"- {item['source']} -> {item.get('preferred', '')}")

    required = ["초인종", "두어 술 떴", "군화", "연립주택", "역병신"]
    missing = [x for x in required if x not in dictionary]

    print(f"package: {out}")

    if missing:
        print("FAIL")
        print("missing:", missing)
        raise SystemExit(2)

    print("PASS")
