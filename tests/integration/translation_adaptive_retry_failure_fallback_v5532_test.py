from __future__ import annotations

from pathlib import Path

from core.translation_quality_v5.best_attempt import (
    AttemptCandidate,
    classify_provider_error,
    select_best_attempt,
    selection_metadata,
)


def _candidate() -> AttemptCandidate:
    issue = {
        "code": "PARAGRAPH_OMISSION_SUSPECTED",
        "severity": "high",
        "retry_required": True,
        "message": "疑似漏段",
    }
    qa = {
        "decision": "retry_required",
        "score": 80,
        "passed": False,
        "issues": [issue],
        "unified_quality_report": {
            "decision": "retry_required",
            "score": 80,
            "merged_issues": [issue],
        },
    }
    return AttemptCandidate(
        qa_attempt=1,
        translation="第一輪較佳候選譯文。",
        qa_report=qa,
        quality_v5_report=None,
        result={"status": "success", "qa_attempt": 1},
    )


def main() -> int:
    candidate = _candidate()
    selected = select_best_attempt([candidate])
    assert selected is candidate

    timeout_error = "NVIDIA API timeout after connect=10s/read=120s"
    meta = selection_metadata(
        [candidate],
        candidate,
        selection_reason="later_provider_error",
        later_provider_error=timeout_error,
        later_qa_attempt=2,
    )
    assert meta["version"] == "5.5.3.2"
    assert meta["selected_qa_attempt"] == 1
    assert meta["selection_reason"] == "later_provider_error"
    assert meta["later_error_type"] == "provider_timeout"
    assert meta["later_qa_attempt"] == 2
    assert classify_provider_error("503 ResourceExhausted") == "provider_capacity"
    assert classify_provider_error("429 rate limit") == "provider_rate_limit"

    runtime_source = Path("lts/txt_translation_runtime.py").read_text(encoding="utf-8")
    assert "best-attempt-fallback" in runtime_source
    assert 'selection_reason="later_provider_error"' in runtime_source
    assert "later_provider_error" in runtime_source
    assert "best_failed_zh.txt" in runtime_source

    print("TE v5.5.3.2 Adaptive Retry Failure Fallback")
    print("================================================")
    print("First successful attempt remains candidate PASS")
    print("Later timeout classified and recorded      PASS")
    print("Later 503/rate-limit classification        PASS")
    print("Runtime fallback wiring present            PASS")
    print("Best failed output path preserved          PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
