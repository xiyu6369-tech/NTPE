from __future__ import annotations

import re
from dataclasses import dataclass

CLI_VERSION = "7.0.0-stage10.3"
_HASH = re.compile(r"^[0-9a-fA-F]{64}$")


@dataclass(frozen=True)
class ControlledCliConfig:
    enabled: bool
    pair_id: str
    run_kind: str
    set_name: str
    chunk_index: int
    source_hash: str
    chunk_hash: str
    model: str
    timeout_seconds: int
    estimated_input_tokens: int
    estimated_output_tokens: int
    minimum_output_tokens: int
    report: str
    resumed: bool = False

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if not self.enabled: blockers.append("controlled-cli-explicit-enable-required")
        if not self.pair_id: blockers.append("controlled-cli-pair-id-required")
        if self.run_kind not in {"baseline", "candidate"}: blockers.append("controlled-cli-run-kind-invalid")
        if not self.set_name: blockers.append("controlled-cli-set-name-required")
        if self.chunk_index < 1: blockers.append("controlled-cli-single-chunk-index-invalid")
        if not _HASH.fullmatch(self.source_hash): blockers.append("controlled-cli-source-hash-invalid")
        if not _HASH.fullmatch(self.chunk_hash): blockers.append("controlled-cli-chunk-hash-invalid")
        if not self.model: blockers.append("controlled-cli-model-required")
        if self.timeout_seconds < 1: blockers.append("controlled-cli-timeout-invalid")
        if min(self.estimated_input_tokens, self.estimated_output_tokens, self.minimum_output_tokens) < 0:
            blockers.append("controlled-cli-token-count-invalid")
        if not self.report: blockers.append("controlled-cli-report-required")
        return tuple(blockers)
