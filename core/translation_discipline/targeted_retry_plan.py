from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .retry_evidence import RetryEvidence

TARGETED_RETRY_PLAN_VERSION = "6.0.0-stage10"


@dataclass(frozen=True)
class TargetedRetryUnit:
    unit_id: str
    source_text: str
    source_start: int
    source_end: int
    paragraph_indexes: tuple[int, ...] = ()
    reason_codes: tuple[str, ...] = ()
    prompt_directives: tuple[str, ...] = ()
    max_provider_attempts: int = 1
    merge_strategy: str = "replace_aligned_range"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_metadata(self, *, include_source_text: bool = False) -> dict[str, Any]:
        result = {
            "unit_id": self.unit_id,
            "source_start": self.source_start,
            "source_end": self.source_end,
            "paragraph_indexes": list(self.paragraph_indexes),
            "reason_codes": list(self.reason_codes),
            "prompt_directives": list(self.prompt_directives),
            "max_provider_attempts": self.max_provider_attempts,
            "provider_attempts": self.max_provider_attempts,
            "merge_strategy": self.merge_strategy,
            "metadata": dict(self.metadata),
        }
        if include_source_text:
            result["source_text"] = self.source_text
        return result


def build_targeted_retry_units(
    source_text: str,
    evidence: Sequence[RetryEvidence],
    *,
    max_units: int = 2,
    attempts_per_unit: int = 1,
) -> tuple[TargetedRetryUnit, ...]:
    reliable = sorted(
        (item for item in evidence if item.reliable and item.has_source_range),
        key=lambda item: (int(item.source_start or 0), int(item.source_end or 0), item.issue_code),
    )
    units: list[TargetedRetryUnit] = []
    for item in reliable:
        start, end = int(item.source_start or 0), int(item.source_end or 0)
        if units and start < units[-1].source_end:
            # Overlapping evidence is ambiguous; do not guess a merge boundary.
            continue
        units.append(TargetedRetryUnit(
            unit_id=f"targeted-{len(units) + 1:03d}",
            source_text=source_text[start:end],
            source_start=start,
            source_end=end,
            paragraph_indexes=item.paragraph_indexes,
            reason_codes=(item.issue_code,),
            prompt_directives=("Regenerate only this source range and preserve its meaning, names, and order.",),
            max_provider_attempts=max(1, int(attempts_per_unit)),
            metadata={"evidence_confidence": item.confidence, **dict(item.metadata)},
        ))
        if len(units) >= max(0, int(max_units)):
            break
    return tuple(units)


def merge_targeted_retry_result(original_text: str, replacement: str, unit: TargetedRetryUnit) -> str | None:
    """Merge only when the QA evidence supplies an explicit translated range.

    Source offsets are never treated as translation offsets. Omission recovery
    may use an explicit translated insertion offset (start == end).
    """
    metadata = dict(unit.metadata)
    start, end = metadata.get("translated_start"), metadata.get("translated_end")
    if isinstance(start, bool) or isinstance(end, bool):
        return None
    if not isinstance(start, int) or not isinstance(end, int):
        return None
    if start < 0 or end < start or end > len(original_text):
        return None
    separator = str(metadata.get("merge_separator") or "")
    return original_text[:start] + separator + str(replacement) + original_text[end:]
