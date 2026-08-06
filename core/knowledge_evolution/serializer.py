"""RM-7.0 Knowledge Evolution Foundation — serializer.

Output formats:
  - JSON (machine-readable, full fidelity)
  - Markdown (human-readable report)
  - Report (executive summary)

No provider. No network. Pure offline serialization.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from .models import (
    AliasEntry,
    EvolutionReport,
    KnowledgeEntity,
    LearningCandidate,
)


def to_json(payload: Any, indent: int = 2) -> str:
    if hasattr(payload, "to_dict"):
        return json.dumps(payload.to_dict(), ensure_ascii=False, indent=indent)
    if isinstance(payload, (list, tuple)):
        items = [
            {k: v for k, v in item.items()} if isinstance(item, dict)
            else item.to_dict() if hasattr(item, "to_dict")
            else str(item)
            for item in payload
        ]
        return json.dumps(items, ensure_ascii=False, indent=indent)
    return json.dumps(payload, ensure_ascii=False, indent=indent)


def entities_to_markdown(entities: List[KnowledgeEntity], title: str = "Knowledge Entities") -> str:
    lines = [f"# {title}", ""]
    for entity in entities:
        lock_status = " [LOCKED]" if entity.is_locked else ""
        lines.append(f"## {entity.canonical} ({entity.source}){lock_status}")
        lines.append(f"- **Type**: {entity.entity_type.value}")
        lines.append(f"- **Priority**: {entity.priority.name}")
        lines.append(f"- **Confidence**: {entity.confidence:.2f}")
        lines.append("")
    return "\n".join(lines)


def aliases_to_markdown(aliases: List[AliasEntry], title: str = "Aliases") -> str:
    lines = [f"# {title}", ""]
    for alias in aliases:
        lines.append(f"- **{alias.alias}** -> {alias.target} (confidence: {alias.confidence:.2f})")
    if not aliases:
        lines.append("*No aliases defined.*")
    return "\n".join(lines)


def report_to_markdown(
    report: EvolutionReport,
    entities: List[KnowledgeEntity],
    candidates: List[LearningCandidate],
    title: str = "Knowledge Evolution Report",
) -> str:
    lines = [
        f"# {title}",
        "",
        f"Generated at: {report.generated_at}",
        "",
        "## Summary",
        f"- New entities: {report.new_entities}",
        f"- Updated entities: {report.updated_entities}",
        f"- Conflicts: {report.conflicts}",
        f"- Promoted candidates: {report.promoted_candidates}",
        f"- Rejected candidates: {report.rejected_candidates}",
        f"- Total entities: {report.total_entities}",
        f"- Total candidates: {report.total_candidates}",
        "",
    ]
    if report.conflicts > 0:
        lines.append("## Conflicts")
        for sample in report.details.get("conflict_samples", []):
            lines.append(
                f"- {sample.get('source')}: expected '{sample.get('expected')}', "
                f"observed '{sample.get('observed')}' [{sample.get('severity')}]"
            )
        lines.append("")

    if entities:
        lines.append(entity_summary_markdown(entities))
    if candidates:
        lines.append(candidates_to_markdown(candidates))

    return "\n".join(lines)


def entity_summary_markdown(entities: List[KnowledgeEntity]) -> str:
    lines = ["## Current Entities", ""]
    for entity in entities:
        lines.append(f"- `{entity.source}` → **{entity.canonical}** [{entity.priority.name}]")
    return "\n".join(lines)


def candidates_to_markdown(candidates: List[LearningCandidate]) -> str:
    lines = ["## Learning Candidates", ""]
    for candidate in candidates:
        status_mark = {
            "PENDING": "[PENDING]",
            "PROMOTED": "[PROMOTED]",
            "REJECTED": "[REJECTED]",
            "EXPIRED": "[EXPIRED]",
        }.get(candidate.status.value, "[?]")
        lines.append(
            f"- `{candidate.source}` → **{candidate.canonical}** "
            f"(conf: {candidate.confidence:.2f}, occ: {candidate.occurrence_count}) {status_mark}"
        )
    return "\n".join(lines)


def full_snapshot_to_json(
    entities_by_tier: Dict[str, List[Dict]],
    candidates: List[Dict],
    aliases: List[Dict],
    conflicts: List[Dict],
) -> str:
    payload = {
        "knowledge_evolution_version": "rm-7.0",
        "entities": entities_by_tier,
        "candidates": candidates,
        "aliases": aliases,
        "conflicts": conflicts,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


class KnowledgeSerializer:
    """Full-fidelity serializer for KnowledgeEvolution state."""

    def __init__(self, store, resolver):
        self._store = store
        self._resolver = resolver

    def to_json(self) -> str:
        from .models import PriorityLevel

        tiers: Dict[str, List[Dict]] = {}
        for tier_name, priority in [
            ("user", PriorityLevel.USER),
            ("runtime", PriorityLevel.RUNTIME),
            ("learning", PriorityLevel.LEARNING),
        ]:
            entities: List[Dict] = []
            for kind in ("characters", "glossary"):
                entities.extend(e.to_dict() for e in self._store.load_entities(priority, kind))
            tiers[tier_name] = entities

        candidates = [c.to_dict() for c in self._store.load_candidates()]
        aliases: List[Dict] = []
        for tier_name, priority in [
            ("user", PriorityLevel.USER),
            ("runtime", PriorityLevel.RUNTIME),
            ("learning", PriorityLevel.LEARNING),
        ]:
            aliases.extend(a.to_dict() for a in self._store.load_aliases(priority))

        payload = {
            "version": "rm-7.0",
            "entities": tiers,
            "candidates": candidates,
            "aliases": aliases,
            "canonicals": self._resolver.list_all_canonicals(),
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        from .models import PRIORITY_ORDER

        lines = ["# Knowledge Evolution System (RM-7.0)", ""]

        for priority in PRIORITY_ORDER:
            tier_name = priority.name
            entities: List[KnowledgeEntity] = []
            for kind in ("characters", "glossary"):
                entities.extend(self._store.load_entities(priority, kind))
            lines.append(f"## {tier_name} Tier ({len(entities)} entries)")
            for entity in entities:
                lock = " [LOCKED]" if entity.is_locked else ""
                lines.append(
                    f"- `{entity.source}` → **{entity.canonical}** "
                    f"(type={entity.entity_type.value}, conf={entity.confidence:.2f}){lock}"
                )
            lines.append("")

        candidates = self._store.load_candidates()
        lines.append(f"## LEARNING CANDIDATES ({len(candidates)} pending)")
        for c in candidates:
            lines.append(
                f"- `{c.source}` → **{c.canonical}** "
                f"(type={c.entity_type.value}, conf={c.confidence:.2f}, "
                f"occ={c.occurrence_count}) [{c.status.value}]"
            )
        lines.append("")

        return "\n".join(lines)

    def to_report(self) -> str:
        from .models import PriorityLevel, utc_now_iso

        user_total = (
            len(self._store.load_entities(PriorityLevel.USER, "characters"))
            + len(self._store.load_entities(PriorityLevel.USER, "glossary"))
        )
        runtime_total = (
            len(self._store.load_entities(PriorityLevel.RUNTIME, "characters"))
            + len(self._store.load_entities(PriorityLevel.RUNTIME, "glossary"))
        )
        learning_total = (
            len(self._store.load_entities(PriorityLevel.LEARNING, "characters"))
            + len(self._store.load_entities(PriorityLevel.LEARNING, "glossary"))
        )

        return "\n".join([
            "# Knowledge Evolution Report",
            f"Generated: {utc_now_iso()}",
            "",
            "Totals:",
            f"  USER:      {user_total}",
            f"  RUNTIME:   {runtime_total}",
            f"  LEARNING:  {learning_total}",
            f"  CANDIDATES: {len(self._store.load_candidates())}",
        ])