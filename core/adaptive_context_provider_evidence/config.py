from __future__ import annotations

import re
from dataclasses import dataclass

_PAIR_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


@dataclass(frozen=True)
class ProviderEvidenceConfig:
    enabled: bool = False
    pair_id: str = ""
    run_kind: str = "baseline"
    real_provider_execution: bool = False

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if not self.enabled:
            blockers.append("provider-evidence-explicit-opt-in-required")
        if not _PAIR_ID.fullmatch(self.pair_id):
            blockers.append("provider-evidence-pair-id-invalid")
        if self.run_kind not in {"baseline", "candidate"}:
            blockers.append("provider-evidence-run-kind-invalid")
        return tuple(blockers)
