from __future__ import annotations

from dataclasses import dataclass

from core.adaptive_context_production_rollout import MAX_ROLLOUT_PERCENT

BENCHMARK_MODES = ("assembly", "provider", "comparison")


@dataclass(frozen=True)
class BenchmarkConfig:
    mode: str
    report: str | None = None
    baseline_stage: str | None = None
    candidate_stage: str | None = None
    target_chunk: int | None = None
    resume_from_stage: str | None = None

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if self.mode not in BENCHMARK_MODES:
            blockers.append("unsupported-benchmark-mode")
        if self.mode == "comparison" and (not self.baseline_stage or not self.candidate_stage):
            blockers.append("comparison-stages-required")
        if self.resume_from_stage and not self.target_chunk:
            blockers.append("resume-target-chunk-required")
        return tuple(blockers)


PRODUCTION_ROLLOUT_MAX_PERCENT = MAX_ROLLOUT_PERCENT
