from __future__ import annotations

from core.translation_discipline import (
    ACCEPT_WITH_WARNINGS,
    PROVIDER_RETRY,
    orchestrate_runtime_discipline,
)


def _issue(code: str, route: str, severity: str = "medium", retry: bool = False) -> dict:
    return {
        "code": code,
        "severity": severity,
        "retry_required": retry,
        "metadata": {"discipline_route": route},
    }


def _runtime_report(*issues: dict, decision: str = "retry_required") -> dict:
    return {
        "passed": decision.startswith("accepted"),
        "decision": decision,
        "retry_required": decision == "retry_required",
        "issues": [],
        "unified_quality_report": {
            "decision": decision,
            "retry_required": decision == "retry_required",
            "merged_issues": list(issues),
        },
    }


def main() -> int:
    calls: list[str] = []

    def revalidate(text: str) -> dict:
        calls.append(text)
        return _runtime_report(_issue("NATURALNESS_GUARD", "local_repair"))

    repaired = orchestrate_runtime_discipline(
        "他請了一周假。",
        _runtime_report(_issue("SIMPLIFIED_CHINESE", "local_repair")),
        revalidate=revalidate,
    )
    assert repaired.text == "他請了一週假。"
    assert repaired.revalidated is True
    assert repaired.final_action == ACCEPT_WITH_WARNINGS
    assert len(calls) == 1
    assert repaired.qa_report["discipline_runtime_orchestrator"]["version"] == "6.0.0-stage06"

    provider = orchestrate_runtime_discipline(
        "譯文",
        _runtime_report(_issue("PARAGRAPH_OMISSION_SUSPECTED", "provider_retry", "high", True)),
        revalidate=lambda text: (_ for _ in ()).throw(AssertionError("provider route must not local-revalidate")),
    )
    assert provider.final_action == PROVIDER_RETRY
    assert provider.revalidated is False

    print("NTPE TE v6.0 Stage 06 Discipline Runtime Orchestrator")
    print("======================================================")
    print("Local repair coordinated once              PASS")
    print("Post-repair revalidation coordinated       PASS")
    print("Final retry decision centralized           PASS")
    print("Provider route bypasses local revalidation PASS")
    print("Runtime metadata recorded                  PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
