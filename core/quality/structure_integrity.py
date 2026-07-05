# =====================================================
# NTPE 1.2 Professional
# Stage-15.5 Formatting / Structure Integrity Engine
# =====================================================

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence


@dataclass
class StructureIssue:
    issue_type: str
    severity: str
    message: str
    line_number: int | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_type": self.issue_type,
            "severity": self.severity,
            "message": self.message,
            "line_number": self.line_number,
            "metadata": dict(self.metadata),
        }


@dataclass
class StructureAnalysis:
    issue_count: int = 0
    warning_count: int = 0
    error_count: int = 0
    critical_count: int = 0
    structure_score: float = 100.0
    source_paragraph_count: int = 0
    target_paragraph_count: int = 0
    source_dialogue_count: int = 0
    target_dialogue_count: int = 0
    source_chapter_marker_count: int = 0
    target_chapter_marker_count: int = 0
    issues: List[StructureIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.error_count == 0 and self.critical_count == 0

    def add_issue(self, issue: StructureIssue) -> None:
        self.issues.append(issue)
        self.issue_count = len(self.issues)
        severity = issue.severity.lower()
        if severity == "critical":
            self.critical_count += 1
            self.structure_score = max(0.0, self.structure_score - 35.0)
        elif severity == "error":
            self.error_count += 1
            self.structure_score = max(0.0, self.structure_score - 15.0)
        else:
            self.warning_count += 1
            self.structure_score = max(0.0, self.structure_score - 5.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_count": self.issue_count,
            "warning_count": self.warning_count,
            "error_count": self.error_count,
            "critical_count": self.critical_count,
            "structure_score": round(float(self.structure_score), 4),
            "passed": self.passed,
            "source_paragraph_count": self.source_paragraph_count,
            "target_paragraph_count": self.target_paragraph_count,
            "source_dialogue_count": self.source_dialogue_count,
            "target_dialogue_count": self.target_dialogue_count,
            "source_chapter_marker_count": self.source_chapter_marker_count,
            "target_chapter_marker_count": self.target_chapter_marker_count,
            "metrics": dict(self.metrics),
            "issues": [issue.to_dict() for issue in self.issues],
        }


class StructureIntegrityAnalyzer:
    """Detect formatting and structural damage in translated output.

    The analyzer is deterministic and provider-independent.  It does not judge
    literary fluency; it validates the transport structure around the text:
    paragraphs, dialogue brackets, placeholders, chapter markers and dangerous
    formatting collapse.
    """

    chapter_patterns: Sequence[re.Pattern[str]] = (
        re.compile(r"^\s*(?:chapter|ch\.)\s*\d+\b", re.IGNORECASE),
        re.compile(r"^\s*(?:第\s*[0-9一二三四五六七八九十百千]+\s*[章話回節])"),
        re.compile(r"^\s*\d+\s*[\.、]\s*.+"),
    )
    placeholder_pattern = re.compile(r"\{[^{}]+\}|%\w|\$\{[^{}]+\}|<[^<>\s]+>")

    def __init__(
        self,
        *,
        paragraph_ratio_min: float = 0.35,
        paragraph_ratio_max: float = 2.8,
        dialogue_ratio_min: float = 0.35,
        dialogue_ratio_max: float = 2.8,
    ) -> None:
        self.paragraph_ratio_min = paragraph_ratio_min
        self.paragraph_ratio_max = paragraph_ratio_max
        self.dialogue_ratio_min = dialogue_ratio_min
        self.dialogue_ratio_max = dialogue_ratio_max

    def analyze(self, source_text: str, translated_text: str) -> StructureAnalysis:
        src = source_text or ""
        dst = translated_text or ""
        analysis = StructureAnalysis()

        src_paragraphs = self._paragraphs(src)
        dst_paragraphs = self._paragraphs(dst)
        analysis.source_paragraph_count = len(src_paragraphs)
        analysis.target_paragraph_count = len(dst_paragraphs)
        analysis.source_dialogue_count = self._dialogue_count(src)
        analysis.target_dialogue_count = self._dialogue_count(dst)
        analysis.source_chapter_marker_count = self._chapter_marker_count(src)
        analysis.target_chapter_marker_count = self._chapter_marker_count(dst)

        self._check_empty_output(src, dst, analysis)
        self._check_paragraph_ratio(analysis)
        self._check_dialogue_ratio(analysis)
        self._check_unbalanced_pairs(dst, analysis)
        self._check_missing_placeholders(src, dst, analysis)
        self._check_chapter_markers(analysis)
        self._check_control_characters(dst, analysis)
        self._check_line_damage(dst, analysis)

        analysis.metrics.update(
            {
                "paragraph_ratio": self._safe_ratio(analysis.target_paragraph_count, analysis.source_paragraph_count),
                "dialogue_ratio": self._safe_ratio(analysis.target_dialogue_count, analysis.source_dialogue_count),
                "structure_score": analysis.structure_score,
                "passed": analysis.passed,
            }
        )
        return analysis

    def _paragraphs(self, text: str) -> List[str]:
        return [part.strip() for part in re.split(r"\n\s*\n+|\r\n\s*\r\n+", text.strip()) if part.strip()]

    def _dialogue_count(self, text: str) -> int:
        # Count common source/target dialogue structures. This remains loose so
        # legacy Korean source with quoted lines can still be compared.
        return text.count("「") + text.count("“") + len(re.findall(r"(^|\n)\s*[-—].+", text))

    def _chapter_marker_count(self, text: str) -> int:
        return sum(
            1
            for line in text.splitlines()
            if any(pattern.search(line.strip()) for pattern in self.chapter_patterns)
        )

    def _safe_ratio(self, numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 1.0 if numerator == 0 else float(numerator)
        return numerator / denominator

    def _check_empty_output(self, src: str, dst: str, analysis: StructureAnalysis) -> None:
        if src.strip() and not dst.strip():
            analysis.add_issue(
                StructureIssue(
                    issue_type="empty_translation_structure",
                    severity="critical",
                    message="Translated text is empty while source text contains structure.",
                )
            )

    def _check_paragraph_ratio(self, analysis: StructureAnalysis) -> None:
        if analysis.source_paragraph_count <= 1:
            return
        ratio = self._safe_ratio(analysis.target_paragraph_count, analysis.source_paragraph_count)
        if ratio < self.paragraph_ratio_min or ratio > self.paragraph_ratio_max:
            analysis.add_issue(
                StructureIssue(
                    issue_type="paragraph_count_drift",
                    severity="error",
                    message="Target paragraph count is outside the allowed source/target ratio.",
                    metadata={
                        "source_paragraph_count": analysis.source_paragraph_count,
                        "target_paragraph_count": analysis.target_paragraph_count,
                        "ratio": ratio,
                    },
                )
            )

    def _check_dialogue_ratio(self, analysis: StructureAnalysis) -> None:
        if analysis.source_dialogue_count <= 1:
            return
        ratio = self._safe_ratio(analysis.target_dialogue_count, analysis.source_dialogue_count)
        if ratio < self.dialogue_ratio_min or ratio > self.dialogue_ratio_max:
            analysis.add_issue(
                StructureIssue(
                    issue_type="dialogue_structure_drift",
                    severity="warning",
                    message="Dialogue marker count changed significantly after translation.",
                    metadata={
                        "source_dialogue_count": analysis.source_dialogue_count,
                        "target_dialogue_count": analysis.target_dialogue_count,
                        "ratio": ratio,
                    },
                )
            )

    def _check_unbalanced_pairs(self, text: str, analysis: StructureAnalysis) -> None:
        pairs = [("「", "」"), ("『", "』"), ("（", "）"), ("(", ")"), ("[", "]")]
        for left, right in pairs:
            l_count = text.count(left)
            r_count = text.count(right)
            if l_count != r_count:
                analysis.add_issue(
                    StructureIssue(
                        issue_type="unbalanced_delimiter",
                        severity="error",
                        message=f"Delimiter pair {left}{right} is unbalanced.",
                        metadata={"left": left, "right": right, "left_count": l_count, "right_count": r_count},
                    )
                )

    def _check_missing_placeholders(self, source_text: str, translated_text: str, analysis: StructureAnalysis) -> None:
        src = set(self.placeholder_pattern.findall(source_text or ""))
        dst = set(self.placeholder_pattern.findall(translated_text or ""))
        missing = sorted(src - dst)
        if missing:
            analysis.add_issue(
                StructureIssue(
                    issue_type="missing_placeholder",
                    severity="error",
                    message="Translated text is missing structural placeholders from source text.",
                    metadata={"missing_placeholders": missing},
                )
            )

    def _check_chapter_markers(self, analysis: StructureAnalysis) -> None:
        if analysis.source_chapter_marker_count and analysis.target_chapter_marker_count == 0:
            analysis.add_issue(
                StructureIssue(
                    issue_type="missing_chapter_marker",
                    severity="warning",
                    message="Source chapter markers were not preserved in translated text.",
                    metadata={
                        "source_chapter_marker_count": analysis.source_chapter_marker_count,
                        "target_chapter_marker_count": analysis.target_chapter_marker_count,
                    },
                )
            )

    def _check_control_characters(self, text: str, analysis: StructureAnalysis) -> None:
        bad = sorted(set(ch for ch in text if ord(ch) < 32 and ch not in "\n\r\t"))
        if bad:
            analysis.add_issue(
                StructureIssue(
                    issue_type="invalid_control_character",
                    severity="error",
                    message="Translated text contains invalid control characters.",
                    metadata={"codepoints": [ord(ch) for ch in bad]},
                )
            )

    def _check_line_damage(self, text: str, analysis: StructureAnalysis) -> None:
        for idx, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if len(stripped) > 5000:
                analysis.add_issue(
                    StructureIssue(
                        issue_type="oversized_line",
                        severity="warning",
                        message="A translated line is unusually long and may indicate paragraph collapse.",
                        line_number=idx,
                        metadata={"length": len(stripped)},
                    )
                )
            if re.search(r"([。！？!?])\1{4,}", stripped):
                analysis.add_issue(
                    StructureIssue(
                        issue_type="punctuation_burst",
                        severity="warning",
                        message="A translated line contains an unusual punctuation burst.",
                        line_number=idx,
                    )
                )
