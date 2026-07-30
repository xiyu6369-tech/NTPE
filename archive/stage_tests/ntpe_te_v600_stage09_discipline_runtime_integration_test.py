from __future__ import annotations

from importlib import import_module
from pathlib import Path

from core.translation_discipline import (
    DisciplineRuntimeContext,
    integrate_translation_discipline_runtime,
    orchestrate_runtime_discipline,
)


def _quality(*issues: dict, decision: str = "accepted", score: int = 100) -> dict:
    return {
        "score": score,
        "decision": decision,
        "accepted": decision.startswith("accepted"),
        "retry_required": decision == "retry_required",
        "merged_issues": list(issues),
    }


def _issue(code: str, severity: str = "medium", retry: bool = False) -> dict:
    return {"code": code, "severity": severity, "retry_required": retry}


def _run(reports: list[dict], text: str = "translation"):
    calls = []
    def quality_runner(candidate: str) -> dict:
        calls.append(candidate)
        return reports[min(len(calls) - 1, len(reports) - 1)]
    result = integrate_translation_discipline_runtime(
        DisciplineRuntimeContext(source_text="source", translated_text=text),
        quality_runner=quality_runner,
        legacy_qa_runner=lambda _text, quality: {
            "unified_quality_report": quality,
            "passed": bool(quality.get("accepted")),
        },
    )
    return result, calls


def main() -> int:
    module_path = Path("core/translation_discipline/runtime_integration.py")
    assert module_path.is_file()
    package = import_module("core.translation_discipline")
    assert package.DisciplineRuntimeContext is DisciplineRuntimeContext
    assert callable(package.integrate_translation_discipline_runtime)

    clean, calls = _run([_quality()])
    assert clean.final_action == "accept" and clean.accepted
    assert not clean.local_repair_applied and not clean.provider_retry_required
    assert len(calls) == 1

    repair, calls = _run([
        _quality(_issue("DIALOGUE_QUOTE_FORMAT"), decision="retry_required", score=90),
        _quality(decision="accepted", score=100),
    ], text="\u201chello\u201d")
    assert repair.initial_action == "local_repair"
    assert repair.local_repair_applied and repair.revalidated
    assert repair.final_action == "accept" and not repair.provider_retry_required
    assert len(calls) == 2

    warning, _ = _run([_quality(_issue("NATURALNESS_GUARD"), decision="accepted_with_warnings", score=95)])
    assert warning.final_text == "translation"
    assert warning.final_action == "accept_with_warnings"
    assert not warning.local_repair_applied

    omission, calls = _run([_quality(_issue("PARAGRAPH_OMISSION_SUSPECTED", "high", True), decision="retry_required", score=60)])
    assert omission.final_action == "provider_retry" and omission.provider_retry_required
    assert "PARAGRAPH_OMISSION_SUSPECTED" in omission.adaptive_feedback["issue_codes"]
    assert not omission.local_repair_applied and len(calls) == 1

    repetition, _ = _run([_quality(_issue("SEMANTIC_DUPLICATE_PARAGRAPH", "high", True), decision="retry_required", score=60)])
    assert repetition.provider_retry_required

    rejected, _ = _run([_quality(_issue("UNKNOWN_CRITICAL", "critical"), decision="retry_required", score=0)])
    assert rejected.final_action == "reject" and rejected.rejected
    assert not rejected.provider_retry_required
    assert rejected.audit_report["initial_action"] == "reject"
    assert rejected.audit_report["final_action"] == "reject"

    legacy = orchestrate_runtime_discipline(
        "translation",
        {"unified_quality_report": _quality()},
    )
    assert legacy.final_action == "accept"

    runtime_source = Path("lts/txt_translation_runtime.py").read_text(encoding="utf-8")
    assert "integrate_translation_discipline_runtime(" in runtime_source
    assert "discipline_outcome = orchestrate_runtime_discipline(" not in runtime_source
    assert "_LOCAL_REPAIR_CODES" not in runtime_source
    assert "requests." not in module_path.read_text(encoding="utf-8")
    assert "TranslationEngine(" not in module_path.read_text(encoding="utf-8")

    print("NTPE TE v6.0 Stage 09 Discipline Runtime Integration")
    print("======================================================")
    print("Single runtime integration entrypoint       PASS")
    print("Quality repair retry feedback audit flow    PASS")
    print("Legacy APIs remain available                PASS")
    print("Import export implementation smoke          PASS")
    print("No provider client or HTTP request          PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
