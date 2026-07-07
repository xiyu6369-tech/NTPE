from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lts.txt_translation_runtime import TxtTranslationOptions, progress_enabled


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    source = root / "tests" / "literary" / "Test_Set_0" / "original_ko.txt"
    options = TxtTranslationOptions(input_path=source, output_dir=root / "work" / "ps04_2_smoke", dry_run=True)
    checks = [
        (source.exists(), "Smoke source exists"),
        (progress_enabled(options), "Progress enabled by default"),
    ]
    failed = False
    print("NTPE PS-04.2 Smoke Test")
    print("========================")
    for ok, label in checks:
        print(f"{label:<28} {'PASS' if ok else 'FAIL'}")
        failed = failed or not ok
    print("PASS" if not failed else "FAIL")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
