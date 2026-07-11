from __future__ import annotations

import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import lts.txt_translation_runtime as runtime
from core.translation_quality_v5.runtime_integration import merge_quality_v5_into_runtime_qa
from core.translation_quality_v5.unified_quality_gate import attach_unified_report
from lts.txt_translation_runtime import TxtTranslationOptions, translate_txt


def _v5_report(*issues: dict, retry_required: bool = False) -> dict:
    return {
        "stage": "TE-v5.3-phase1",
        "status": "accepted" if not issues else "repair_required",
        "accepted": not issues,
        "retry_required": retry_required,
        "quality_score": 100 if not issues else 80,
        "safe_replacements": [],
        "issues": list(issues),
    }


def _assert_unified_contract() -> None:
    legacy_failure = {
        "passed": False,
        "enabled": True,
        "issues": [{"code": "KOREAN_RESIDUE", "message": "legacy failure"}],
        "metrics": {},
    }
    merged = merge_quality_v5_into_runtime_qa(
        legacy_failure,
        _v5_report(),
        attempt=1,
        chunk_id="chunk-1",
    )
    assert merged["decision"] == "retry_required"
    assert merged["score"] < 100
    assert merged["passed"] is False

    duplicate = merge_quality_v5_into_runtime_qa(
        legacy_failure,
        _v5_report({
            "code": "hangul_residue",
            "severity": "critical",
            "message": "v5 failure",
            "repair_action": "retranslate_residual_spans",
        }, retry_required=True),
    )
    duplicate_issues = duplicate["unified_quality_report"]["merged_issues"]
    assert len(duplicate_issues) == 1
    assert duplicate_issues[0]["code"] == "HANGUL_RESIDUE"
    assert duplicate_issues[0]["metadata"]["sources"] == [
        "translation_quality_v5", "legacy_runtime_qa"
    ]

    warnings = merge_quality_v5_into_runtime_qa(
        {"passed": True, "enabled": True, "issues": [], "metrics": {}},
        _v5_report({
            "code": "duplicate_line",
            "severity": "medium",
            "message": "review repetition",
            "repair_action": "quality_review",
        }),
    )
    assert warnings["decision"] == "accepted_with_warnings"
    assert warnings["passed"] is True
    assert warnings["score"] < 100

    clean = merge_quality_v5_into_runtime_qa(
        {"passed": True, "enabled": True, "issues": [], "metrics": {}},
        _v5_report(),
    )
    assert clean["decision"] == "accepted"
    assert clean["score"] == 100
    assert clean["issues"] == []

    opaque_failure = merge_quality_v5_into_runtime_qa(
        {"passed": True, "enabled": True, "issues": [], "metrics": {}},
        {**_v5_report(), "accepted": False, "status": "repair_required"},
    )
    assert opaque_failure["decision"] == "retry_required"
    assert opaque_failure["score"] < 100

    legacy_only = merge_quality_v5_into_runtime_qa(legacy_failure, {})
    assert legacy_only["decision"] == "retry_required"
    assert legacy_only["unified_quality_report"]["quality_v5_enabled"] is False

    augmented = attach_unified_report(
        _v5_report(), merged["unified_quality_report"]
    )
    assert augmented["quality_score"] == 100  # Phase 1 compatibility field.
    assert augmented["score"] < 100  # Unified score is authoritative.
    assert augmented["decision"] == "retry_required"
    assert augmented["legacy_qa_issues"]


def _assert_report_disable_keeps_decision() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "NTPE"
        root.mkdir()
        source = root / "sample.txt"
        source.write_text("이것은 짧은 원문입니다.\n", encoding="utf-8")

        class FakeEngine:
            def __init__(self, root=None):
                self.root = root

            def translate_package(self, package, package_path=None):
                output = root / "provider_output.txt"
                output.write_text(
                    "這是一段完整、自然且符合要求的繁體中文譯文。\n",
                    encoding="utf-8",
                )
                return {"status": "success", "output_path": str(output)}

        original_engine = runtime.TranslationEngine
        runtime.TranslationEngine = FakeEngine
        try:
            result = translate_txt(
                TxtTranslationOptions(
                    input_path=source,
                    output_dir=root / "out",
                    quality_v5_report_enabled=False,
                    qa_attempts=1,
                    retry_base_seconds=0,
                    progress_enabled=False,
                ),
                root=root,
            )
        finally:
            runtime.TranslationEngine = original_engine

        assert result["status"] == "success"
        assert result["records"][0]["qa"]["decision"] == "accepted"
        assert not list((root / "out").rglob("*quality_v5_attempt*.json"))


def main() -> int:
    _assert_unified_contract()
    _assert_report_disable_keeps_decision()
    print("NTPE TE v5.3.1 Unified Quality Gate Test")
    print("=========================================")
    print("Legacy failure overrides v5 acceptance  PASS")
    print("Cross-system issues deduplicate          PASS")
    print("Warnings use explicit decision           PASS")
    print("Critical and high issues request retry   PASS")
    print("Clean output scores 100 and is accepted  PASS")
    print("Quality v5 disabled keeps Legacy QA      PASS")
    print("Report disabled keeps gate decision      PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
