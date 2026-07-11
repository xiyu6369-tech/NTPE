from __future__ import annotations

from pathlib import Path

from core.translation_discipline import orchestrate_runtime_discipline


def _issue(code: str, route: str) -> dict:
    return {"code": code, "severity": "medium", "metadata": {"discipline_route": route}}


def test_stage06_runtime_uses_single_discipline_orchestrator() -> None:
    runtime = {
        "passed": False,
        "decision": "retry_required",
        "retry_required": True,
        "issues": [],
        "unified_quality_report": {
            "decision": "retry_required",
            "retry_required": True,
            "merged_issues": [_issue("SIMPLIFIED_CHINESE", "local_repair")],
        },
    }

    outcome = orchestrate_runtime_discipline(
        "一周",
        runtime,
        revalidate=lambda text: {
            "passed": True,
            "decision": "accepted",
            "retry_required": False,
            "issues": [],
            "unified_quality_report": {
                "decision": "accepted",
                "retry_required": False,
                "merged_issues": [],
            },
        },
    )
    assert outcome.text == "一週"
    assert outcome.qa_report["decision"] == "accepted"
    assert outcome.qa_report["discipline_runtime_orchestrator"]["revalidated"] is True

    source = Path("lts/txt_translation_runtime.py").read_text(encoding="utf-8")
    assert "orchestrate_runtime_discipline(" in source
    assert "apply_adaptive_local_repairs(" not in source
    assert "apply_adaptive_retry_decision(" not in source
    assert "discipline-runtime-orchestrator" in source
