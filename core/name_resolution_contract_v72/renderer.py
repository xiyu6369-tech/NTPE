from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .eligibility import mapping_exclusion_reasons
from .models import NameResolutionRecord


@dataclass(frozen=True)
class RenderingEvidence:
    eligible_mappings: tuple[dict[str, object], ...]
    excluded_mappings: tuple[dict[str, object], ...]
    unresolved_names: tuple[str, ...]
    conflict_names: tuple[str, ...]
    rendered_mappings: tuple[str, ...]
    token_estimate: int
    token_budget: int
    budget_exhausted: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "eligible_mappings": list(self.eligible_mappings),
            "excluded_mappings": list(self.excluded_mappings),
            "unresolved_names": list(self.unresolved_names),
            "conflict_names": list(self.conflict_names),
            "rendered_mappings": list(self.rendered_mappings),
            "token_estimate": self.token_estimate, "token_budget": self.token_budget,
            "budget_exhausted": self.budget_exhausted,
        }


def _estimate_tokens(line: str) -> int:
    return max(1, (len(line) + 3) // 4)


def render_prompt_mappings(
    records: Iterable[NameResolutionRecord],
    *,
    source_first_occurrence: dict[str, int] | None = None,
    token_budget: int = 128,
) -> tuple[str, RenderingEvidence]:
    occurrence = source_first_occurrence or {}
    ordered = sorted(
        tuple(records),
        key=lambda item: (
            occurrence.get(item.normalized_source_name, 2**31 - 1),
            item.normalized_source_name,
            item.deterministic_fingerprint,
        ),
    )
    eligible: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []
    unresolved: list[str] = []
    conflicts: list[str] = []
    rendered: list[str] = []
    used = 0
    exhausted = False
    for record in ordered:
        reasons = mapping_exclusion_reasons(record)
        if reasons:
            excluded.append({"source_name": record.source_name, "reasons": list(reasons)})
            if record.conflict_state: conflicts.append(record.source_name)
            else: unresolved.append(record.source_name)
            continue
        line = f"- {record.source_name} → {record.approved_zh_hant_name}"
        estimate = _estimate_tokens(line)
        item = {"source_name": record.source_name, "target_name": record.approved_zh_hant_name,
                "fingerprint": record.deterministic_fingerprint, "token_estimate": estimate}
        eligible.append(item)
        if used + estimate <= token_budget:
            rendered.append(line)
            used += estimate
        else:
            exhausted = True
            excluded.append({"source_name": record.source_name, "reasons": ["mapping_budget_exhausted"]})
    text = "" if not rendered else "人物姓名固定譯名：\n" + "\n".join(rendered)
    evidence = RenderingEvidence(
        tuple(eligible), tuple(excluded), tuple(unresolved), tuple(conflicts),
        tuple(rendered), used, token_budget, exhausted,
    )
    return text, evidence
