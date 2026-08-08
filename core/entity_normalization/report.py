"""RM-7.3 Entity Normalization Reporting.

Generates reports on normalization results and conflicts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import (
    ConflictRecord,
    ConflictSeverity,
    EntityType,
    NormalizationResult,
    NormalizedEntity,
    ResolutionSource,
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class NormalizationReport:
    """Report for a single normalization run."""
    total_entities: int = 0
    normalized_count: int = 0
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    by_type: Dict[str, Dict[str, int]] = field(default_factory=dict)
    by_form_type: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=utc_now_iso)

    @property
    def conflict_count(self) -> int:
        return len(self.conflicts)

    @property
    def high_severity_conflicts(self) -> int:
        return sum(1 for c in self.conflicts if c.get("severity") == ConflictSeverity.HIGH.value)

    @property
    def unresolved_conflicts(self) -> int:
        return sum(1 for c in self.conflicts if not c.get("resolution"))

    def add_entity(self, entity: NormalizedEntity) -> "NormalizationReport":
        new_by_type = dict(self.by_type)
        type_key = entity.entity_type.value
        if type_key not in new_by_type:
            new_by_type[type_key] = {"total": 0, "normalized": 0}
        new_by_type[type_key]["total"] += 1
        new_by_type[type_key]["normalized"] += 1

        new_by_form = dict(self.by_form_type)
        form_key = entity.matched_form.form_type.value
        new_by_form[form_key] = new_by_form.get(form_key, 0) + 1

        return NormalizationReport(
            total_entities=self.total_entities + 1,
            normalized_count=self.normalized_count + 1,
            conflicts=list(self.conflicts),
            by_type=new_by_type,
            by_form_type=new_by_form,
            metadata=dict(self.metadata),
            generated_at=utc_now_iso(),
        )

    def add_conflict(self, conflict: ConflictRecord) -> "NormalizationReport":
        return NormalizationReport(
            total_entities=self.total_entities,
            normalized_count=self.normalized_count,
            conflicts=self.conflicts + [conflict.to_dict()],
            by_type=dict(self.by_type),
            by_form_type=dict(self.by_form_type),
            metadata=dict(self.metadata),
            generated_at=utc_now_iso(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_entities": self.total_entities,
            "normalized_count": self.normalized_count,
            "conflict_count": self.conflict_count,
            "high_severity_conflicts": self.high_severity_conflicts,
            "unresolved_conflicts": self.unresolved_conflicts,
            "conflicts": list(self.conflicts),
            "by_type": dict(self.by_type),
            "by_form_type": dict(self.by_form_type),
            "metadata": dict(self.metadata),
            "generated_at": self.generated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NormalizationReport":
        return cls(
            total_entities=int(data.get("total_entities", 0)),
            normalized_count=int(data.get("normalized_count", 0)),
            conflicts=list(data.get("conflicts", [])),
            by_type=dict(data.get("by_type", {})),
            by_form_type=dict(data.get("by_form_type", {})),
            metadata=dict(data.get("metadata", {})),
            generated_at=str(data.get("generated_at", utc_now_iso())),
        )


class NormalizationReporter:
    """Generates normalization reports from results."""

    def __init__(self):
        self._report = NormalizationReport()

    def generate(self, result: NormalizationResult) -> NormalizationReport:
        """Generate report from NormalizationResult."""
        report = NormalizationReport(
            total_entities=len(result.entities),
            normalized_count=len(result.entities),
            metadata=dict(result.metadata),
        )

        for entity in result.entities:
            report = report.add_entity(entity)

        for conflict in result.conflicts:
            report = report.add_conflict(conflict)

        self._report = report
        return report

    def get_report(self) -> NormalizationReport:
        return self._report

    def clear(self) -> None:
        self._report = NormalizationReport()


def build_prompt_section(report: NormalizationReport) -> str:
    """Build a prompt section for translation engine.

    This is the upgraded prompt format from RM-7.3 spec.
    """
    lines = [
        "=== ENTITY NORMALIZATION ===",
        "",
        "Entity Identity & Name Forms:",
        "",
    ]

    # Group by entity
    entities_by_id: Dict[str, List[Dict[str, Any]]] = {}
    for conflict in report.conflicts:
        # Conflicts don't have entity_id directly, skip for now
        pass

    # Build from by_type summary
    for entity_type, stats in report.by_type.items():
        lines.append(f"## {entity_type}")
        lines.append(f"  Total: {stats['total']}, Normalized: {stats['normalized']}")
        lines.append("")

    lines.append("Name Form Distribution:")
    for form_type, count in report.by_form_type.items():
        lines.append(f"  {form_type}: {count}")

    if report.conflicts:
        lines.append("")
        lines.append("Conflicts Detected:")
        for conflict in report.conflicts:
            lines.append(f"  Source: {conflict['source']}")
            lines.append(f"  Candidates: {', '.join(conflict['candidates'])}")
            lines.append(f"  Severity: {conflict['severity']}")
            if conflict.get('resolution'):
                lines.append(f"  Resolution: {conflict['resolution']} ({conflict.get('resolution_source', 'AUTO')})")
            lines.append("")

    lines.append("")
    lines.append("Usage Rules:")
    lines.append("- Preserve original address level")
    lines.append("- Do not expand given name into full name")
    lines.append("- Do not replace intimate forms with full names")
    lines.append("- Use the exact translation for each surface form")

    return "\n".join(lines)


def build_compact_prompt_section(result: NormalizationResult) -> str:
    """Build compact prompt section for injection.

    Queries the global identity registry so that ALL known name forms of an
    entity (Full / Given / Family / Formal / Intimate) are included even when
    the current chunk only extracted a subset of surface forms.

    Format:
    Entity Normalization:

    Entity: 정태의
    Canonical: 鄭泰義
    Forms:
      FULL_NAME: 정태의 → 鄭泰義
      GIVEN_NAME: 태의 → 泰義
      FORMAL: 정 씨 → 鄭先生
      INTIMATE: 태의야 → 泰義啊

    Rules:
    - Preserve address level
    - No given→full expansion
    - No intimate→full replacement
    """
    # Import here to avoid circular imports
    from .identity import get_identity_registry
    from .models import NameFormType

    lines = [
        "Entity Normalization:",
        "",
    ]

    # Collect every entity_id referenced in the result, plus every registered
    # entity that was created during this run. The registry is the source of
    # truth for ALL known forms; the result only carries current-chunk hits.
    referenced_ids: set = set()
    for entity in result.entities:
        referenced_ids.add(entity.entity_id)

    registry = get_identity_registry()
    registered_entities = {e.entity_id: e for e in registry.get_all_entities()}

    # Prefer canonical entities (full registry view), but fall back to the
    # first NormalizedEntity in result if the registry was cleared.
    entity_ids = list(referenced_ids)
    for rid in referenced_ids:
        if rid in registered_entities:
            entity_ids.append(rid)

    seen_ids: set = set()
    for entity_id in entity_ids:
        if entity_id in seen_ids:
            continue
        seen_ids.add(entity_id)

        canonical = registered_entities.get(entity_id)
        # Build a complete forms view from the registry (all known forms),
        # so Given / Formal / Intimate always appear if registered.
        forms_by_type: Dict[NameFormType, "object"] = {}
        if canonical:
            nf = canonical.name_forms
            for ft in (
                NameFormType.FULL_NAME,
                NameFormType.GIVEN_NAME,
                NameFormType.FAMILY_NAME,
                NameFormType.FORMAL,
                NameFormType.INTIMATE,
            ):
                form = nf.get_form(ft)
                if form is not None:
                    forms_by_type[ft] = form
            for nick in nf.nicknames:
                forms_by_type.setdefault(NameFormType.NICKNAME, nick)
            entity_label = canonical.source_name
            entity_canonical = canonical.canonical_translation
        else:
            # Registry miss: use first NormalizedEntity of this id as fallback.
            fallback = next(
                (ne for ne in result.entities if ne.entity_id == entity_id),
                None,
            )
            if not fallback:
                continue
            entity_label = fallback.source_text
            entity_canonical = fallback.translation
            ft = fallback.matched_form.form_type
            forms_by_type.setdefault(ft, fallback.matched_form)

        lines.append(f"Entity: {entity_label}")
        lines.append(f"Canonical: {entity_canonical}")
        lines.append("Forms:")

        # Render forms in a stable order: Full, Given, Family, Formal, Intimate
        # then nicknames.
        order = [
            NameFormType.FULL_NAME,
            NameFormType.GIVEN_NAME,
            NameFormType.FAMILY_NAME,
            NameFormType.FORMAL,
            NameFormType.INTIMATE,
            NameFormType.NICKNAME,
        ]
        for ft in order:
            form = forms_by_type.get(ft)
            if form is None:
                continue
            lines.append(f"  {ft.value}: {form.source} → {form.translation}")

        lines.append("")

    lines.append("Rules:")
    lines.append("- Preserve address level")
    lines.append("- No given→full expansion")
    lines.append("- No intimate→full replacement")

    return "\n".join(lines)


__all__ = [
    "NormalizationReport",
    "NormalizationReporter",
    "build_prompt_section",
    "build_compact_prompt_section",
]