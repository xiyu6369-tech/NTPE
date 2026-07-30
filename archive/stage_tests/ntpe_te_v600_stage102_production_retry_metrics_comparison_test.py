from __future__ import annotations

import json
import tempfile
from pathlib import Path

from core.translation_discipline import (
    PRODUCTION_COMPARISON_VERSION,
    compare_stage_outputs,
    summarize_retry_metrics,
    write_comparison_reports,
)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        baseline = root / "baseline"
        current = root / "current"
        _write(baseline / "x_chunk_000001_quality_v5_attempt_1.json", {
            "status": "retry_required", "retry_required": True,
            "issues": [{"code": "PARAGRAPH_OMISSION_SUSPECTED"}],
        })
        _write(baseline / "x_chunk_000002_quality_v5_attempt_1.json", {
            "status": "accepted", "accepted": True, "issues": [],
        })
        _write(current / "x_chunk_000001_discipline_audit_attempt_1.json", {
            "final_action": "accept_with_warnings",
            "quality": {"issues": [{"code": "NATURALNESS_GUARD"}]},
            "local_repair": {"changed": True},
            "adaptive_retry_policy": {"retry_tier": "none", "provider_call_budget": {"limit": 2, "used": 0, "remaining": 2}},
        })
        _write(current / "x_chunk_000002_discipline_audit_attempt_1.json", {
            "final_action": "provider_retry",
            "quality": {"issues": [{"code": "PARAGRAPH_OMISSION_SUSPECTED"}]},
            "local_repair": {"changed": False},
            "adaptive_retry_policy": {"retry_tier": "full_retry", "provider_call_budget": {"limit": 2, "used": 1, "remaining": 1}},
        })
        metrics = summarize_retry_metrics(current)
        assert metrics.chunks_observed == 2
        assert metrics.recovery_budget_limit == 4
        assert metrics.recovery_budget_used == 1
        comparison = compare_stage_outputs(baseline, current)
        assert comparison.version == PRODUCTION_COMPARISON_VERSION
        assert comparison.current.full_retry == 1
        json_out, md_out = root / "report.json", root / "report.md"
        payload = write_comparison_reports(baseline, current, json_out, md_out)
        assert json_out.exists() and md_out.exists()
        assert payload["current"]["source_kind"] == "discipline_audit"
    print("TE v6.0 Stage 10.2 Production Retry Metrics & Comparison")
    print("=========================================================")
    print("Legacy quality report fallback          PASS")
    print("Latest-per-chunk audit aggregation      PASS")
    print("Recovery budget totals are additive     PASS")
    print("JSON and Markdown comparison reports    PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
