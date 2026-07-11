from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json

PRODUCTION_VALIDATION_VERSION = "6.0.0-stage10.1"

@dataclass
class ProductionValidationSummary:
    version: str = PRODUCTION_VALIDATION_VERSION
    audit_reports: int = 0
    accepted: int = 0
    accepted_with_warnings: int = 0
    provider_retry: int = 0
    targeted_retry: int = 0
    full_retry: int = 0
    local_repair: int = 0
    rejected: int = 0
    provider_budget_limit: int = 0
    provider_budget_used: int = 0
    provider_budget_remaining: int = 0
    issue_codes: dict[str, int] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["issue_codes"] = dict(sorted((self.issue_codes or {}).items()))
        return data


def summarize_stage_output(stage_dir: str | Path) -> ProductionValidationSummary:
    root = Path(stage_dir)
    summary = ProductionValidationSummary(issue_codes={})
    for path in root.rglob("*_discipline_audit_attempt_*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        summary.audit_reports += 1
        final_action = str(payload.get("final_action") or "")
        if final_action == "accept": summary.accepted += 1
        elif final_action == "accept_with_warnings": summary.accepted_with_warnings += 1
        elif final_action == "provider_retry": summary.provider_retry += 1
        elif final_action == "reject": summary.rejected += 1
        policy = dict(payload.get("adaptive_retry_policy") or {})
        tier = str(policy.get("retry_tier") or "")
        if tier == "targeted_retry": summary.targeted_retry += 1
        elif tier == "full_retry": summary.full_retry += 1
        repair = dict(payload.get("local_repair") or {})
        if repair.get("changed"): summary.local_repair += 1
        budget = dict(policy.get("provider_call_budget") or {})
        summary.provider_budget_limit = max(summary.provider_budget_limit, int(budget.get("limit") or 0))
        summary.provider_budget_used = max(summary.provider_budget_used, int(budget.get("used") or 0))
        summary.provider_budget_remaining = max(summary.provider_budget_remaining, int(budget.get("remaining") or 0))
        for issue in (payload.get("quality") or {}).get("issues") or []:
            code = str(issue.get("code") or "UNKNOWN")
            summary.issue_codes[code] = summary.issue_codes.get(code, 0) + 1
    return summary


def write_validation_report(stage_dir: str | Path, output_path: str | Path) -> dict[str, Any]:
    summary = summarize_stage_output(stage_dir).to_dict()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
