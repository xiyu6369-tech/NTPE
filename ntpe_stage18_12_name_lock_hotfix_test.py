from pathlib import Path

from lts.txt_translation_runtime import (
    apply_locked_dictionary,
    build_prompt_package,
    TxtTranslationOptions,
)


def check(name, ok):
    print(f"{name:<36} {'PASS' if ok else 'FAIL'}")
    if not ok:
        raise SystemExit(1)


def main():
    locked = {"정태의": "鄭泰義"}
    fixed = apply_locked_dictionary("定泰義看著정태의。正太義沉默。", locked)
    check("Korean source lock", "정태의" not in fixed and fixed.count("鄭泰義") == 3)
    check("Wrong Chinese alias lock", "定泰義" not in fixed and "正太義" not in fixed)

    options = TxtTranslationOptions(input_path=Path("passion6.txt"), output_dir=Path("output"))
    package = build_prompt_package(
        options=options,
        chunk_text="정태의는 잠시 고개를 들었다.",
        chunk_index=1,
        chunk_total=1,
        locked_dictionary=locked,
    )
    prompt = package["prompt"]["user_prompt"]
    check("Prompt includes locked name", "정태의 → 鄭泰義" in prompt)
    check("Prompt blocks 定泰義", "定泰義" in prompt and "鄭泰義" in prompt)
    print("PASS")


if __name__ == "__main__":
    main()
