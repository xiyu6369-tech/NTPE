from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


HOOK_VERSION = "lcr-batch10.1-hook-1.0"
HOOK_SYMBOL = "after_chunk_package_prepared"


@dataclass(frozen=True)
class HookEvidence:
    hook_id: str
    shadow_status: str
    input_fingerprint: str
    modules_evaluated: tuple[str, ...]
    provider_requests_executed: int
    production_output_changed: bool
    baseline_changed: bool
    warnings: tuple[str, ...]
    blocking_reasons: tuple[str, ...]
    result_discarded: bool
    duration_ms: float
    created_at: str


@dataclass(frozen=True)
class HookOutcome:
    status: str
    baseline_continues: bool
    evidence: HookEvidence | None
    before_hash: str
    after_hash: str
    prompt_before_hash: str
    prompt_after_hash: str
    provider_identity_before: str
    provider_identity_after: str
    resume_before_hash: str
    resume_after_hash: str
    output_contract_before_hash: str
    output_contract_after_hash: str
    warning_codes: tuple[str, ...] = ()
    result_discarded: bool = False


@dataclass(frozen=True)
class ExtendedShadowGate:
    status: str
    requirements: Mapping[str, bool]
    reasons: tuple[str, ...]
    active_production_authorized: bool = False
