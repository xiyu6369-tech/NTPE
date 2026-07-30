from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeReadinessEvidenceCollector


ROOT = Path(__file__).resolve().parent
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def _complete_inputs() -> dict:
    return {
        "freezes": {f"TE-v3.{version}": True for version in range(2, 7)},
        "checks": {
            "feature_flag_present": True,
            "disabled_guard_present": True,
            "optin_hook_present": True,
            "preflight_present": True,
            "boundary_regression_present": True,
        },
        "versions": {"scheduler": "TE-v3.2", "preflight": "TE-v3.6"},
        "reports": {"freeze": {"status": "pass"}, "preflight": {"ready": True}},
    }


def test_evidence_collector_empty_partial_and_complete_inputs() -> None:
    collector = RuntimeReadinessEvidenceCollector()

    empty = collector.collect()
    assert empty["missing_sections"] == ["freezes", "checks", "versions", "reports"]
    assert collector.summarize(empty)["complete"] is False
    assert collector.validate_evidence(empty)["valid"] is True

    partial = collector.collect({"freezes": {"TE-v3.6": True}})
    assert partial["collected_freezes"] == {"TE-v3.6": True}
    assert partial["missing_sections"] == ["checks", "versions", "reports"]

    complete = collector.collect(_complete_inputs())
    summary = collector.summarize(complete)
    assert complete["missing_sections"] == []
    assert summary == {
        "freezes_count": 5,
        "checks_count": 5,
        "reports_count": 2,
        "complete": True,
        "missing_sections": [],
    }
    assert collector.validate_evidence(complete)["valid"] is True


def test_evidence_collector_removes_raw_text_recursively() -> None:
    collector = RuntimeReadinessEvidenceCollector()
    supplied = _complete_inputs()
    supplied["reports"]["unsafe"] = {
        "source_text": "secret source",
        "text": "secret output",
        "nested": {"chunks": ["secret chunk"], "status": "ignored_raw_fields"},
    }
    evidence = collector.collect(supplied)
    serialized = repr(evidence)

    assert "secret source" not in serialized
    assert "secret output" not in serialized
    assert "secret chunk" not in serialized
    assert evidence["collected_reports"]["unsafe"] == {
        "nested": {"status": "ignored_raw_fields"}
    }
    assert collector.validate_evidence(evidence)["valid"] is True

    unsafe = {**evidence, "collected_reports": {"text": "raw"}}
    validation = collector.validate_evidence(unsafe)
    assert validation["valid"] is False
    assert any("forbidden raw field" in error for error in validation["errors"])


def test_evidence_collector_has_no_external_side_effects() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    watched = ["core.translation_engine.provider_runtime", "lts.txt_translation_runtime", "requests", "httpx"]
    before = {name: name in sys.modules for name in watched}
    try:
        collector = RuntimeReadinessEvidenceCollector()
        evidence = collector.collect(_complete_inputs())
        assert collector.validate_evidence(evidence)["valid"] is True
        assert os.environ.get("NVIDIA_API_KEY") is None
        assert {name: name in sys.modules for name in watched} == before
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key


def main() -> int:
    test_evidence_collector_empty_partial_and_complete_inputs()
    test_evidence_collector_removes_raw_text_recursively()
    test_evidence_collector_has_no_external_side_effects()
    print("NTPE TE-v3.7 Stage-3.7.3 Runtime Readiness Evidence Collector PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
