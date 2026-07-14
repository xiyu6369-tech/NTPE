from __future__ import annotations

from dataclasses import dataclass

PIPELINE_VERSION = "7.0.0-stage10.7"


@dataclass(frozen=True)
class ProviderEvidencePipelineConfig:
    enabled: bool = False
    declared_provenance: str = "mock"
    single_chunk_only: bool = True
    preserve_payload_required: bool = True
    preserve_prompt_required: bool = True

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if not self.enabled:
            blockers.append("provider-evidence-pipeline-explicit-opt-in-required")
        if self.declared_provenance not in {"mock", "real"}:
            blockers.append("provider-evidence-pipeline-provenance-invalid")
        if not self.single_chunk_only:
            blockers.append("provider-evidence-pipeline-single-chunk-required")
        if not self.preserve_payload_required:
            blockers.append("provider-evidence-pipeline-payload-preservation-required")
        if not self.preserve_prompt_required:
            blockers.append("provider-evidence-pipeline-prompt-preservation-required")
        return tuple(blockers)
