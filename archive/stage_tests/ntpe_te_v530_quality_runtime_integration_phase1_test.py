from __future__ import annotations

import json
import tempfile
from pathlib import Path

from core.translation_quality_v5.runtime_integration import (
    merge_quality_v5_into_runtime_qa,
    run_quality_v5_phase1,
)
from lts.txt_translation_runtime import TxtTranslationOptions, parse_args


def main() -> int:
    source = "정태의는 일주일 동안 섬에 머물렀다.\n\n그는 고개를 끄덕였다."
    translated = "鄭泰義在島上待了一周。\n\n他點了點頭。"
    report = run_quality_v5_phase1(
        source,
        translated,
        locked_terms={"정태의": "鄭泰義"},
    )
    assert report["stage"] == "TE-v5.3-phase1"
    assert report["normalized_text"] == "鄭泰義在島上待了一週。\n\n他點了點頭。"
    assert report["runtime_integration"]["provider_called"] is False
    assert report["runtime_integration"]["semantic_rewrite_allowed"] is False
    assert report["safe_replacements"]

    bad = run_quality_v5_phase1(source, "정태의", locked_terms={"정태의": "鄭泰義"})
    merged = merge_quality_v5_into_runtime_qa(
        {"passed": True, "issues": [], "metrics": {}}, bad
    )
    assert merged["passed"] is False
    assert any(i["code"] == "V5_HANGUL_RESIDUE" for i in merged["issues"])

    options = parse_args(["input.txt", "output"])
    assert options.quality_v5_enabled is True
    assert options.quality_v5_report_enabled is True
    disabled = parse_args([
        "input.txt", "output", "--no-quality-v5", "--no-quality-v5-report"
    ])
    assert disabled.quality_v5_enabled is False
    assert disabled.quality_v5_report_enabled is False

    print("NTPE TE v5.3 Quality Runtime Integration Phase 1 Test")
    print("======================================================")
    print("Conservative normalization applied       PASS")
    print("No semantic rewrite/provider call        PASS")
    print("Critical v5 issue blocks Runtime QA      PASS")
    print("Quality integration enabled by default   PASS")
    print("Immediate disable switches available     PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
