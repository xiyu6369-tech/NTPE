from __future__ import annotations

import json
from pathlib import Path

from .model import ActivationEvidence, ActivationPolicyDecision


def load_activation_evidence(ab_report_path: str | Path, canary_report_path: str | Path) -> ActivationEvidence:
    ab = json.loads(Path(ab_report_path).read_text(encoding="utf-8"))
    canary = json.loads(Path(canary_report_path).read_text(encoding="utf-8"))
    return ActivationEvidence(
        ab_ready=bool(ab.get("ready", False)),
        ab_status=str(ab.get("status", "")),
        canary_status=str(canary.get("status", "")),
        canary_activated_records=int(canary.get("activated_records", 0) or 0),
        estimated_tokens_saved=int(canary.get("estimated_tokens_saved", 0) or 0),
        provider_calls_added=int(canary.get("provider_calls_added", 0) or 0),
        target_chunk_completed=bool(canary.get("target_chunk_completed", False)),
        fallback_reasons=tuple(str(x) for x in canary.get("fallback_reasons", []) if str(x)),
    )


def write_activation_policy_report(decision: ActivationPolicyDecision, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(decision.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target
