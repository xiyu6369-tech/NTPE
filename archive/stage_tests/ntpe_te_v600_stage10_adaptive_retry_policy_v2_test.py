from __future__ import annotations

from importlib import import_module
from pathlib import Path

from core.translation_discipline import (
    AdaptiveRetryPolicy,
    DisciplineRuntimeContext,
    ProviderCallBudget,
    integrate_translation_discipline_runtime,
    merge_targeted_retry_result,
)


def issue(code: str, severity: str = "high", *, evidence: dict | None = None, retry: bool = True) -> dict:
    value = {"code": code, "severity": severity, "retry_required": retry}
    if evidence is not None:
        value["evidence"] = evidence
    return value


def report(*issues: dict, decision: str = "retry_required", score: int = 60) -> dict:
    return {"merged_issues": list(issues), "decision": decision, "score": score, "retry_required": decision == "retry_required"}


def main() -> int:
    policy = AdaptiveRetryPolicy()
    assert policy.plan(report(decision="accepted", score=100), source_text="abc").tier == "none"
    assert policy.plan(report(issue("SIMPLIFIED_CHINESE", "medium", retry=False), decision="accepted_with_warnings"), source_text="abc").tier == "local_repair"
    natural = policy.plan(report(issue("NATURALNESS_GUARD", "medium", retry=False), decision="accepted_with_warnings"), source_text="abc")
    assert natural.tier == "none" and not natural.targeted_retry_units

    source = "first paragraph\n\nsecond paragraph"
    start = source.index("second")
    reliable = {"source_start": start, "source_end": len(source), "paragraph_indexes": [1], "confidence": 0.95, "reliable": True, "translated_start": 4, "translated_end": 4, "merge_separator": "\n"}
    targeted = policy.plan(report(issue("PARAGRAPH_OMISSION_SUSPECTED", evidence=reliable)), source_text=source)
    assert targeted.tier == "targeted_retry" and len(targeted.targeted_retry_units) == 1
    unit = targeted.targeted_retry_units[0]
    assert unit.source_text == "second paragraph" and unit.source_start == start
    assert merge_targeted_retry_result("first", "second", unit) == "firs\nsecondt"
    assert policy.plan(report(issue("PARAGRAPH_OMISSION_SUSPECTED")), source_text=source).tier == "full_retry"
    assert policy.plan(report(issue("SEMANTIC_DUPLICATE_PARAGRAPH", evidence=reliable)), source_text=source).tier == "targeted_retry"
    assert policy.plan(report(issue("HALLUCINATION")), source_text=source).tier == "full_retry"
    assert policy.plan(report(issue("UNKNOWN_CRITICAL", "critical")), source_text=source).tier == "reject"

    budget = ProviderCallBudget(limit=2).spend().spend()
    assert budget.used == 2 and budget.remaining == 0 and not budget.can_spend()
    try:
        budget.spend()
        raise AssertionError("budget exceeded without failure")
    except ValueError:
        pass

    calls: list[str] = []
    def quality_runner(text: str) -> dict:
        calls.append(text)
        return report(issue("PARAGRAPH_OMISSION_SUSPECTED", evidence=reliable))
    runtime = integrate_translation_discipline_runtime(
        DisciplineRuntimeContext(source_text=source, translated_text="first", runtime_metadata={"provider_call_budget_limit": 2}),
        quality_runner=quality_runner,
        legacy_qa_runner=lambda _text, quality: {"unified_quality_report": quality, "passed": False},
    )
    assert runtime.final_action == "provider_retry"  # Stage 09 compatibility
    assert runtime.retry_tier == "targeted_retry" and runtime.targeted_retry_required
    assert not runtime.full_retry_required and runtime.provider_call_budget["remaining"] == 2
    assert runtime.audit_report["adaptive_retry_policy"]["targeted_unit_count"] == 1

    package = import_module("core.translation_discipline")
    for name in ("AdaptiveRetryPolicy", "RetryEvidence", "TargetedRetryUnit", "build_adaptive_retry_plan"):
        assert getattr(package, name)
    for path in (
        "core/translation_discipline/adaptive_retry_policy.py",
        "core/translation_discipline/retry_evidence.py",
        "core/translation_discipline/targeted_retry_plan.py",
    ):
        assert Path(path).is_file()
    runtime_source = Path("lts/txt_translation_runtime.py").read_text(encoding="utf-8")
    assert "NTPE_NVIDIA_RPM_LIMIT" not in runtime_source or "40" in runtime_source
    assert "requests." not in Path("core/translation_discipline/adaptive_retry_policy.py").read_text(encoding="utf-8")

    print("NTPE TE v6.0 Stage 10 Adaptive Retry Policy 2.0")
    print("================================================")
    print("Three-tier policy and reliable evidence      PASS")
    print("Provider recovery budget                     PASS")
    print("Stage 09 API compatibility                   PASS")
    print("Import/export and implementation packaging   PASS")
    print("No provider client or HTTP request           PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
