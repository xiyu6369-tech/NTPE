from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lts.txt_translation_runtime import TxtTranslationOptions, analyze_translation_quality


def main() -> int:
    options = TxtTranslationOptions(input_path=Path("input.txt"), output_dir=Path("output"), simplified_chinese_policy="normalize")
    qa = analyze_translation_quality("그는 말했다.", "他说話了。", options)
    ok = qa["passed"] and qa["metrics"]["simplified_hits"] >= 0
    print("Stage-18.14 Integration", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
