import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lts.txt_translation_runtime import apply_locked_dictionary, build_prompt_package, TxtTranslationOptions


def main():
    locked = {"정태의": "鄭泰義"}
    text = apply_locked_dictionary("정태의 / 定泰義 / 鄭太義", locked)
    assert text == "鄭泰義 / 鄭泰義 / 鄭泰義"
    pkg = build_prompt_package(
        options=TxtTranslationOptions(input_path=Path("input.txt"), output_dir=Path("output")),
        chunk_text="정태의",
        chunk_index=1,
        chunk_total=1,
        locked_dictionary=locked,
    )
    assert "禁止使用" in pkg["prompt"]["user_prompt"]
    assert "定泰義" in pkg["prompt"]["user_prompt"]
    print("PASS")


if __name__ == "__main__":
    main()
