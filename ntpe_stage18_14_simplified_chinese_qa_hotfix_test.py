from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lts.txt_translation_runtime import (
    TxtTranslationOptions,
    analyze_translation_quality,
    format_translation_output,
)


def main() -> int:
    source = "그는 문을 열었다."
    translated = "他说着话打开门。"
    options = TxtTranslationOptions(input_path=Path("input.txt"), output_dir=Path("output"))
    normalized = format_translation_output(translated, options)
    qa = analyze_translation_quality(source, normalized, options)

    checks = [
        ("Taiwan Traditional normalization", "打开" not in normalized and "他说" not in normalized and "门" not in normalized),
        ("Simplified does not fail by default", qa.get("passed") is True),
        ("Simplified metrics visible", "simplified_hits" in qa.get("metrics", {})),
    ]

    print("NTPE Stage-18.14 Simplified Chinese QA Hotfix Test")
    print("=" * 56)
    failed = False
    for name, ok in checks:
        print(f"{name:<36} {'PASS' if ok else 'FAIL'}")
        failed = failed or not ok
    print("PASS" if not failed else "FAIL")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
