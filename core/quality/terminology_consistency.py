# =====================================================
# NTPE 1.2 Professional
# Stage-15.3 Terminology / Character Consistency Engine
# =====================================================

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


@dataclass(frozen=True)
class TerminologyEntry:
    """Canonical terminology mapping for a source term or character name."""

    source: str
    canonical: str
    aliases: Tuple[str, ...] = ()
    category: str = "terminology"
    case_sensitive: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, source: str, value: Any) -> "TerminologyEntry":
        if isinstance(value, TerminologyEntry):
            return value
        if isinstance(value, str):
            return cls(source=source, canonical=value)
        if isinstance(value, Mapping):
            return cls(
                source=str(value.get("source", source)),
                canonical=str(value.get("canonical") or value.get("target") or value.get("translation") or ""),
                aliases=tuple(str(a) for a in value.get("aliases", ()) if str(a)),
                category=str(value.get("category", "terminology")),
                case_sensitive=bool(value.get("case_sensitive", True)),
                metadata=dict(value.get("metadata", {})),
            )
        raise TypeError(f"Unsupported terminology entry value for {source!r}: {type(value)!r}")

    def target_forms(self) -> Tuple[str, ...]:
        return tuple(dict.fromkeys((self.canonical, *self.aliases)))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "canonical": self.canonical,
            "aliases": list(self.aliases),
            "category": self.category,
            "case_sensitive": self.case_sensitive,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class TerminologyIssue:
    entry: TerminologyEntry
    issue_type: str
    severity: str
    message: str
    source_count: int = 0
    canonical_count: int = 0
    alias_counts: Dict[str, int] = field(default_factory=dict)
    observed_forms: Tuple[str, ...] = ()
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.entry.source,
            "canonical": self.entry.canonical,
            "category": self.entry.category,
            "issue_type": self.issue_type,
            "severity": self.severity,
            "message": self.message,
            "source_count": self.source_count,
            "canonical_count": self.canonical_count,
            "alias_counts": dict(self.alias_counts),
            "observed_forms": list(self.observed_forms),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class TerminologyAnalysis:
    entries_checked: int
    issues: List[TerminologyIssue]
    metrics: Dict[str, Any]

    @property
    def passed(self) -> bool:
        return not any(issue.severity in {"error", "critical"} for issue in self.issues)

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "warning")

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity in {"error", "critical"})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "entries_checked": self.entries_checked,
            "warning_count": self.warning_count,
            "error_count": self.error_count,
            "issues": [issue.to_dict() for issue in self.issues],
            "metrics": dict(self.metrics),
        }


class TerminologyConsistencyAnalyzer:
    """Deterministic glossary and character-name consistency analyzer.

    The analyzer is provider-independent and does not call any AI model. It
    compares source-term occurrence against translated canonical forms and
    known aliases, then reports missing canonical terms and translation drift.
    """

    def __init__(
        self,
        entries: Optional[Iterable[TerminologyEntry | Tuple[str, str] | Mapping[str, Any]]] = None,
        *,
        strict_aliases: bool = True,
        minimum_source_count: int = 1,
    ) -> None:
        self.strict_aliases = strict_aliases
        self.minimum_source_count = max(1, int(minimum_source_count))
        self.entries: List[TerminologyEntry] = []
        if entries:
            for entry in entries:
                self.add_entry(entry)

    @classmethod
    def from_glossary(cls, glossary: Mapping[str, Any], **kwargs: Any) -> "TerminologyConsistencyAnalyzer":
        analyzer = cls(**kwargs)
        for source, value in glossary.items():
            analyzer.add_entry(TerminologyEntry.from_mapping(str(source), value))
        return analyzer

    def add_entry(self, entry: TerminologyEntry | Tuple[str, str] | Mapping[str, Any]) -> None:
        if isinstance(entry, TerminologyEntry):
            normalized = entry
        elif isinstance(entry, tuple) and len(entry) == 2:
            normalized = TerminologyEntry(source=str(entry[0]), canonical=str(entry[1]))
        elif isinstance(entry, Mapping):
            source = str(entry.get("source") or entry.get("term") or "")
            if not source:
                raise ValueError("Terminology mapping entry requires a source term.")
            normalized = TerminologyEntry.from_mapping(source, entry)
        else:
            raise TypeError(f"Unsupported terminology entry: {entry!r}")
        if normalized.source and normalized.canonical:
            self.entries.append(normalized)

    def analyze(self, source_text: str, translated_text: str) -> TerminologyAnalysis:
        source_text = source_text or ""
        translated_text = translated_text or ""
        issues: List[TerminologyIssue] = []
        checked = 0
        total_source_hits = 0
        total_canonical_hits = 0

        for entry in self.entries:
            source_count = self._count(source_text, entry.source, entry.case_sensitive)
            if source_count < self.minimum_source_count:
                continue
            checked += 1
            total_source_hits += source_count
            canonical_count = self._count(translated_text, entry.canonical, entry.case_sensitive)
            total_canonical_hits += canonical_count
            alias_counts = {
                alias: self._count(translated_text, alias, entry.case_sensitive)
                for alias in entry.aliases
                if alias
            }
            observed = tuple(form for form, count in ((entry.canonical, canonical_count), *alias_counts.items()) if count > 0)

            if canonical_count == 0 and not any(alias_counts.values()):
                issues.append(
                    TerminologyIssue(
                        entry=entry,
                        issue_type="missing_canonical_translation",
                        severity="error",
                        message="Source term appears but no canonical translation or accepted alias was found.",
                        source_count=source_count,
                        canonical_count=canonical_count,
                        alias_counts=alias_counts,
                        observed_forms=observed,
                    )
                )
                continue

            if self.strict_aliases and any(alias_counts.values()):
                used_aliases = {k: v for k, v in alias_counts.items() if v > 0}
                issues.append(
                    TerminologyIssue(
                        entry=entry,
                        issue_type="alias_or_drift_detected",
                        severity="warning",
                        message="Translation used a non-canonical alias for a locked terminology entry.",
                        source_count=source_count,
                        canonical_count=canonical_count,
                        alias_counts=used_aliases,
                        observed_forms=observed,
                    )
                )

            if canonical_count > 0 and source_count > 0 and canonical_count < max(1, source_count // 2):
                issues.append(
                    TerminologyIssue(
                        entry=entry,
                        issue_type="low_canonical_coverage",
                        severity="warning",
                        message="Canonical translation appears significantly fewer times than the source term.",
                        source_count=source_count,
                        canonical_count=canonical_count,
                        alias_counts=alias_counts,
                        observed_forms=observed,
                        metadata={"coverage_ratio": round(canonical_count / max(1, source_count), 4)},
                    )
                )

        coverage = total_canonical_hits / max(1, total_source_hits)
        metrics = {
            "configured_entries": len(self.entries),
            "entries_checked": checked,
            "total_source_hits": total_source_hits,
            "total_canonical_hits": total_canonical_hits,
            "canonical_coverage_ratio": round(float(coverage), 4),
            "strict_aliases": self.strict_aliases,
            "minimum_source_count": self.minimum_source_count,
        }
        return TerminologyAnalysis(entries_checked=checked, issues=issues, metrics=metrics)

    def _count(self, text: str, needle: str, case_sensitive: bool) -> int:
        if not needle:
            return 0
        flags = 0 if case_sensitive else re.IGNORECASE
        return len(re.findall(re.escape(needle), text or "", flags=flags))


def build_default_character_glossary() -> Dict[str, Dict[str, Any]]:
    """Small built-in compatibility glossary used by launcher smoke tests.

    Runtime users can pass their own glossary/profile; this default does not
    alter existing behavior and is intentionally minimal.
    """

    return {
        "정태의": {"canonical": "鄭泰義", "aliases": ["正太義", "鄭太義"], "category": "character"},
        "일라이": {"canonical": "伊萊", "aliases": ["伊來", "伊萊伊"], "category": "character"},
        "카일": {"canonical": "凱爾", "aliases": ["卡爾", "凱勒"], "category": "character"},
    }
