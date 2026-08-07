"""RM-7.1 Consistency Reporter — produce human-readable and JSON reports.

Takes a list of EntityMatch and EntityMismatch, categorises by
EntityCategory, and emits a structured text report.

- Read-only: never mutates knowledge, glossaries, or translations.
- Two output formats: plain-text summary and JSON dict.
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any, Dict, List, Optional, Sequence

from core.entity_consistency.models import (
    ConsistencyReport,
    EntityCategory,
    EntityMatch,
    EntityMismatch,
    ReportSeverity,
)

CATEGORY_LABEL: Dict[EntityCategory, str] = {
    EntityCategory.CHARACTER:    "Characters",
    EntityCategory.LOCATION:     "Locations",
    EntityCategory.ORGANIZATION: "Organizations",
    EntityCategory.TERM:         "Terms",
}

_CATEGORY_ORDER: tuple[EntityCategory, ...] = (
    EntityCategory.CHARACTER,
    EntityCategory.LOCATION,
    EntityCategory.ORGANIZATION,
    EntityCategory.TERM,
)


class ConsistencyReporter:
    """Aggregate matches/mismatches and produce formatted output."""

    def __init__(self) -> None:
        self._matches: List[EntityMatch] = []
        self._mismatches: List[EntityMismatch] = []

    def add_match(self, m: EntityMatch) -> None:
        self._matches.append(m)

    def add_mismatch(self, m: EntityMismatch) -> None:
        self._mismatches.append(m)

    def add_all(self, matches: List[EntityMatch], mismatches: List[EntityMismatch]) -> None:
        self._matches.extend(matches)
        self._mismatches.extend(mismatches)

    def clear(self) -> None:
        self._matches.clear()
        self._mismatches.clear()

    # ------------------------------------------------------------------
    # Text Report
    # ------------------------------------------------------------------

    def render(self, title: str = "Entity Consistency Report") -> str:
        """Return a formatted plain-text consistency report."""
        lines: List[str] = []
        lines.append(title)
        lines.append("=" * len(title))
        lines.append("")

        cat_pass: Dict[str, int] = {}
        cat_warn: Dict[str, int] = {}
        cat_error: Dict[str, int] = {}

        for m in self._matches:
            cat = m.category if hasattr(m, "category") else EntityCategory.TERM
            cat_pass[cat.value] = cat_pass.get(cat.value, 0) + 1

        for m in self._mismatches:
            cat = m.category if hasattr(m, "category") else EntityCategory.TERM
            sev = m.severity.value.upper() if hasattr(m, "severity") else "ERROR"
            if sev in ("HIGH", "ERROR"):
                cat_error[cat.value] = cat_error.get(cat.value, 0) + 1
            elif sev == "MEDIUM":
                cat_warn[cat.value] = cat_warn.get(cat.value, 0) + 1
            else:
                cat_warn[cat.value] = cat_warn.get(cat.value, 0) + 1

        for cat in _CATEGORY_ORDER:
            label = CATEGORY_LABEL.get(cat, cat.value)
            p = cat_pass.get(cat.value, 0)
            w = cat_warn.get(cat.value, 0)
            e = cat_error.get(cat.value, 0)
            if p == 0 and w == 0 and e == 0:
                continue
            lines.append(label)
            lines.append("-" * len(label))
            lines.append(f"PASS    {p}")
            lines.append(f"WARNING {w}")
            lines.append(f"ERROR   {e}")
            lines.append("")

        lines.append("Summary")
        lines.append("-------")
        lines.append(f"Total Matches:   {len(self._matches)}")
        lines.append(f"Total Mismatches: {len(self._mismatches)}")
        lines.append("")

        if self._mismatches:
            lines.append("Details")
            lines.append("-------")
            for m in self._mismatches:
                lines.append(
                    f"[{m.severity.value}] {m.entity_type.value}: "
                    f'expected="{m.expected}" found="{m.found}" (source: {m.source})'
                )

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # JSON Report
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "matches": [m.to_dict() for m in self._matches],
            "mismatches": [m.to_dict() for m in self._mismatches],
            "totals": {
                "match": len(self._matches),
                "mismatch": len(self._mismatches),
            },
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_report(self) -> ConsistencyReport:
        """Build the encoded ConsistencyReport model."""
        cat_summary: Dict[str, Dict[str, int]] = {}
        for cat in _CATEGORY_ORDER:
            cat_summary[cat.value] = {"PASS": 0, "WARNING": 0, "ERROR": 0}

        for m in self._matches:
            cat_key = m.category.value
            if cat_key not in cat_summary:
                continue
            cat_summary[cat_key]["PASS"] += 1

        for m in self._mismatches:
            cat_key = m.category.value
            if cat_key not in cat_summary:
                continue
            sev = m.severity
            if sev.value in ("HIGH", "ERROR"):
                cat_summary[cat_key]["ERROR"] += 1
            else:
                cat_summary[cat_key]["WARNING"] += 1

        report = ConsistencyReport(
            total_scanned=len(self._matches) + len(self._mismatches),
            matches=[m.to_dict() for m in self._matches],
            mismatches=[m.to_dict() for m in self._mismatches],
        )
        return report.with_summary(cat_summary)


# -- module-level convenience --------------------------------------------

_reporters: Dict[str, ConsistencyReporter] = {}


def get_reporter(name: str = "default") -> ConsistencyReporter:
    if name not in _reporters:
        _reporters[name] = ConsistencyReporter()
    return _reporters[name]


def clear_all() -> None:
    _reporters.clear()