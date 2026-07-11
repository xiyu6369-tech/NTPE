from __future__ import annotations

from pathlib import Path

from lts.txt_translation_runtime import (
    _adaptive_retry_budget_metadata,
    resolve_adaptive_retry_execution_mode,
)


def main() -> int:
    assert resolve_adaptive_retry_execution_mode(
        qa_attempt=2,
        retry_policy={"tier": "targeted_retry"},
        has_attempt_candidate=True,
        legacy_segment_recovery_applicable=True,
    ) == "targeted_retry"
    assert resolve_adaptive_retry_execution_mode(
        qa_attempt=2,
        retry_policy={"tier": "full_retry"},
        has_attempt_candidate=True,
        legacy_segment_recovery_applicable=True,
    ) == "full_retry"
    assert resolve_adaptive_retry_execution_mode(
        qa_attempt=2,
        retry_policy={},
        has_attempt_candidate=True,
        legacy_segment_recovery_applicable=True,
    ) == "legacy_segment_recovery"
    assert resolve_adaptive_retry_execution_mode(
        qa_attempt=2,
        retry_policy={"tier": "reject"},
        has_attempt_candidate=True,
        legacy_segment_recovery_applicable=True,
    ) == "reject"
    assert _adaptive_retry_budget_metadata({"provider_call_budget": {"limit": 2}}, 1) == {
        "limit": 2,
        "used": 1,
        "remaining": 1,
    }
    assert _adaptive_retry_budget_metadata({"provider_call_budget": {"limit": 2}}, 3) == {
        "limit": 2,
        "used": 3,
        "remaining": 0,
    }

    source = Path("lts/txt_translation_runtime.py").read_text(encoding="utf-8")
    assert "adaptive-retry-policy " in source
    assert 'package["prompt_runtime"]["adaptive_retry_policy"] = discipline_result.adaptive_retry_plan' in source
    assert 'recovery_mode == "full_retry"' in source
    assert 'recovery_mode == "legacy_segment_recovery"' in source
    assert source.index('recovery_mode == "full_retry"') < source.index('recovery_mode == "legacy_segment_recovery"')
    assert '"version": "6.0.0-stage10.1.1"' in source

    print("TE v6.0 Stage 10.1.1 Adaptive Retry Plan Runtime Wiring Fix")
    print("============================================================")
    print("Targeted tier outranks legacy recovery      PASS")
    print("Full tier outranks legacy recovery          PASS")
    print("Legacy recovery requires missing v10 plan   PASS")
    print("Provider budget persists across recovery    PASS")
    print("Runtime plan metadata and logging wired     PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
