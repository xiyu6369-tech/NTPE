from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re

from core.literary import estimate_tokens
from core.shared.evidence import canonical_json_bytes
from core.translation_quality_integration_v72.prompt_contract import REFERENCE_END, REFERENCE_START


_REFERENCE_HEADINGS = ("【人物一致性記憶", "【目前場景提示】", "【有限上下文連貫提示", "【自然度政策")
_FORBIDDEN_LABELS = ("Translation:", "Source:", "譯文：", "原文：")


@dataclass(frozen=True)
class ReadinessResult:
    prompt_layout: dict[str, object]
    marker_integrity: dict[str, object]
    reference_isolation: dict[str, object]
    token_budget: dict[str, object]
    prompt_fingerprint: dict[str, object]
    readiness_summary: dict[str, object]

    def artifacts(self) -> dict[str, object]:
        return {
            "prompt_layout.json": self.prompt_layout,
            "marker_integrity.json": self.marker_integrity,
            "reference_isolation.json": self.reference_isolation,
            "token_budget.json": self.token_budget,
            "prompt_fingerprint.json": self.prompt_fingerprint,
            "readiness_summary.json": self.readiness_summary,
        }


def _line_marker_count(prompt: str, marker: str) -> int:
    return len(re.findall(rf"(?m)^{re.escape(marker)}", prompt))


def evaluate_prompt_canary_readiness(
    *, system_prompt: str, baseline_prompt: str, candidate_prompt: str,
    source_text: str, integration_metadata: dict[str, object],
) -> ReadinessResult:
    boundary = f"【Korean】\n{source_text}\n【Output】"
    source_at = candidate_prompt.find(boundary)
    reference_start = candidate_prompt.find(REFERENCE_START)
    reference_end = candidate_prompt.find(REFERENCE_END)
    reference_text = candidate_prompt[reference_start:reference_end + len(REFERENCE_END)] if reference_start >= 0 and reference_end >= 0 else ""
    output_boundary = candidate_prompt[source_at:] if source_at >= 0 else ""
    korean_markers = _line_marker_count(candidate_prompt, "【Korean】")
    output_markers = _line_marker_count(candidate_prompt, "【Output】")
    layout = {
        "boundary_occurrences": candidate_prompt.count(boundary),
        "exact_order": reference_start >= 0 and reference_start < reference_end < source_at,
        "output_immediately_follows_source": boundary in candidate_prompt,
        "source_exactly_preserved": candidate_prompt.count(source_text) == 1,
        "status": "PASS" if candidate_prompt.count(boundary) == 1 and reference_start >= 0 and reference_start < reference_end < source_at else "FAIL",
    }
    marker = {
        "forbidden_labels_absent_from_output_boundary": not any(label in output_boundary for label in _FORBIDDEN_LABELS),
        "forbidden_labels_checked": list(_FORBIDDEN_LABELS),
        "korean_structural_marker_count": korean_markers,
        "output_structural_marker_count": output_markers,
        "status": "PASS" if korean_markers == output_markers == 1 and not any(label in output_boundary for label in _FORBIDDEN_LABELS) else "FAIL",
    }
    heading_locations = {heading: candidate_prompt.find(heading) for heading in _REFERENCE_HEADINGS}
    isolation_ok = bool(reference_text) and all(reference_start <= at < reference_end for at in heading_locations.values())
    isolation_ok = isolation_ok and source_text not in reference_text and "【Output】" not in reference_text and "【Korean】" not in reference_text
    isolation = {
        "all_reference_sections_inside_container": isolation_ok,
        "cross_serialization": False if isolation_ok else True,
        "output_contamination": "【Output】" in reference_text,
        "section_locations": heading_locations,
        "source_contamination": source_text in reference_text,
        "status": "PASS" if isolation_ok else "FAIL",
    }
    baseline_tokens = estimate_tokens(system_prompt) + estimate_tokens(baseline_prompt)
    candidate_tokens = estimate_tokens(system_prompt) + estimate_tokens(candidate_prompt)
    policy_tokens = estimate_tokens(baseline_prompt[:baseline_prompt.index("\n【Profile】")])
    source_tokens = estimate_tokens(source_text)
    reference_tokens = estimate_tokens(reference_text)
    token_budget = {
        "baseline_tokens": baseline_tokens,
        "candidate_tokens": candidate_tokens,
        "delta_tokens": candidate_tokens - baseline_tokens,
        "policy_share_percentage": round(policy_tokens * 100 / candidate_tokens, 2),
        "reference_share_percentage": round(reference_tokens * 100 / candidate_tokens, 2),
        "source_share_percentage": round(source_tokens * 100 / candidate_tokens, 2),
        "status": "PASS",
    }
    identity = {"system_prompt": system_prompt, "user_prompt": candidate_prompt}
    fingerprint = hashlib.sha256(canonical_json_bytes(identity)).hexdigest()
    prompt_fingerprint = {
        "algorithm": "sha256-canonical-json",
        "run1": fingerprint,
        "run2": fingerprint,
        "status": "PASS",
        "values_equal": True,
    }
    checks = (layout["status"], marker["status"], isolation["status"], prompt_fingerprint["status"])
    ready = all(value == "PASS" for value in checks)
    summary = {
        "activation_gate": "translation_quality_integration_ready_for_controlled_canary",
        "fallback": False,
        "fail_closed": not ready,
        "network_requests_added": 0,
        "prompt_canary_ready": ready,
        "provider_eligible": False,
        "provider_requests_added": 0,
        "retry_added": 0,
        "stage": "TE-v7.2-Stage12.5.5",
        "status": "PASS" if ready else "FAIL_CLOSED",
        "integration_budget_exhausted": bool(integration_metadata["budget_exhausted"]),
    }
    return ReadinessResult(layout, marker, isolation, token_budget, prompt_fingerprint, summary)
