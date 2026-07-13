from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .model import RolloutRecord

METRICS_VERSION = "7.0.0-stage08.4"


@dataclass
class RolloutMetrics:
    total_packages: int = 0
    eligible_packages: int = 0
    sampled_packages: int = 0
    activated_packages: int = 0
    fallback_packages: int = 0
    disabled_packages: int = 0
    kill_switch_blocks: int = 0
    policy_blocks: int = 0
    strategy_blocks: int = 0
    budget_blocks: int = 0
    anchor_blocks: int = 0
    admission_blocks: int = 0
    baseline_context_tokens: int = 0
    ace_context_tokens: int = 0
    estimated_tokens_saved: int = 0
    payload_changed_records: int = 0
    payload_unchanged_records: int = 0
    provider_calls_added: int = 0
    qa_accepted: int = 0
    qa_retry_required: int = 0
    qa_failed: int = 0
    provider_timeout: int = 0
    provider_503: int = 0
    rollout_bucket: int = -1
    rollout_percent: int = 0
    policy_version: str = "7.0.0-stage08.4"
    strategy_version: str = "7.0.0-stage08.3"
    records: list[dict[str, object]] = field(default_factory=list)

    def observe(self, record: RolloutRecord) -> None:
        self.total_packages += 1
        self.rollout_bucket = record.rollout_bucket
        self.rollout_percent = record.rollout_percent
        self.policy_version = record.policy_version
        self.strategy_version = record.strategy_version
        if record.decision not in {"disabled", "blocked"}:
            self.eligible_packages += 1
        if record.decision in {"sampled", "activated", "fallback", "shadow-compatible"}:
            self.sampled_packages += 1
        if record.activated:
            self.activated_packages += 1
        if record.fallback_used:
            self.fallback_packages += 1
        if record.decision in {"disabled", "blocked", "not-sampled"}:
            self.disabled_packages += 1
        for blocker in record.blockers:
            if "kill-switch" in blocker:
                self.kill_switch_blocks += 1
            elif "policy" in blocker:
                self.policy_blocks += 1
            elif "strategy" in blocker:
                self.strategy_blocks += 1
            elif "budget" in blocker:
                self.budget_blocks += 1
            elif "anchor" in blocker:
                self.anchor_blocks += 1
            else:
                self.admission_blocks += 1
        self.baseline_context_tokens += record.baseline_context_tokens
        self.ace_context_tokens += record.ace_context_tokens
        self.estimated_tokens_saved += record.estimated_tokens_saved
        self.payload_changed_records += int(record.payload_changed)
        self.payload_unchanged_records += int(not record.payload_changed)
        self.provider_calls_added += record.provider_calls_added
        self.records.append(record.to_dict())

    def observe_provider(self, status: str) -> None:
        normalized = str(status).strip().lower()
        if normalized == "timeout":
            self.provider_timeout += 1
        elif normalized in {"503", "http_503"}:
            self.provider_503 += 1

    def observe_qa(self, status: str) -> None:
        normalized = str(status).strip().lower()
        if normalized in {"accepted", "pass", "pass_with_warning"}:
            self.qa_accepted += 1
        elif normalized in {"retry", "retry_required"}:
            self.qa_retry_required += 1
        elif normalized in {"failed", "fail"}:
            self.qa_failed += 1

    def to_dict(self) -> dict[str, object]:
        saved = max(0, self.estimated_tokens_saved)
        ratio = round(saved / self.baseline_context_tokens, 6) if self.baseline_context_tokens else 0.0
        values = {key: value for key, value in vars(self).items() if key != "records"}
        return {
            "version": METRICS_VERSION,
            "mode": "production_canary" if self.activated_packages else "disabled",
            **values,
            "estimated_reduction_ratio": ratio,
            "records": list(self.records),
            "content_redacted": True,
        }


def write_metrics_report(metrics: RolloutMetrics, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(metrics.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target
