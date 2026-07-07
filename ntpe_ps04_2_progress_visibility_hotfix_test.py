from __future__ import annotations

import io
import contextlib
from pathlib import Path
from lts.txt_translation_runtime import TxtTranslationOptions, translate_txt


def main() -> int:
    root = Path(__file__).resolve().parent
    source = root / "tests" / "literary" / "Test_Set_0" / "original_ko.txt"
    out = root / "work" / "ps04_2_progress_test"
    out.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    options = TxtTranslationOptions(
        input_path=source,
        output_dir=out,
        dry_run=True,
        progress_enabled=True,
        quality_profile="literary",
    )
    with contextlib.redirect_stdout(buf):
        result = translate_txt(options, root=root)
    text = buf.getvalue()
    checks = [
        (result.get("status") == "success", "Dry run translation succeeds"),
        ("[NTPE PROGRESS] read input" in text, "Read progress emitted"),
        ("chunk plan" in text, "Chunk plan emitted"),
        ("chunk 1/" in text, "Chunk progress emitted"),
        ((out / "original_ko_live_progress.json").exists(), "Live progress JSON written"),
    ]
    failed = False
    print("NTPE PS-04.2 Progress Visibility Hotfix Test")
    print("================================================")
    for ok, label in checks:
        print(f"{label:<32} {'PASS' if ok else 'FAIL'}")
        failed = failed or not ok
    print("PASS" if not failed else "FAIL")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
