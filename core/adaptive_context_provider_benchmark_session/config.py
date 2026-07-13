from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ControlledSessionConfig:
    enabled: bool = False
    pair_id: str = ""
    run_kind: str = "baseline"
    execution_mode: str = "mock"
    real_provider_execution: bool = False
    single_chunk_only: bool = True

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if not self.enabled: blockers.append("controlled-session-explicit-opt-in-required")
        if not self.pair_id: blockers.append("controlled-session-pair-id-required")
        if self.run_kind not in {"baseline", "candidate"}: blockers.append("controlled-session-run-kind-invalid")
        if self.execution_mode not in {"mock", "real"}: blockers.append("controlled-session-execution-mode-invalid")
        if self.execution_mode == "real" and not self.real_provider_execution:
            blockers.append("real-provider-execution-flag-required")
        if self.execution_mode == "mock" and self.real_provider_execution:
            blockers.append("mock-session-cannot-claim-real-provider")
        if not self.single_chunk_only: blockers.append("controlled-session-single-chunk-boundary-required")
        return tuple(blockers)
