from __future__ import annotations

from .model import BenchmarkRun


def validate_run_role(run: BenchmarkRun) -> tuple[str, ...]:
    blockers: list[str] = []
    if run.run_kind == "baseline" and run.contract.ace_enabled:
        blockers.append("baseline-ace-must-be-disabled")
    elif run.run_kind == "candidate":
        if not run.contract.ace_enabled:
            blockers.append("candidate-ace-production-rollout-required")
        if run.contract.rollout_percent < 1 or run.contract.rollout_percent > 5:
            blockers.append("candidate-rollout-percent-invalid")
    else:
        if run.run_kind not in {"baseline", "candidate"}:
            blockers.append("benchmark-run-kind-invalid")
    return tuple(blockers)
