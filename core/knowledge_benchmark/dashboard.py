"""
Dashboard Generator (RM-5.8.5)

Produces dashboard.md and dashboard.json from a scorecard and regression analysis.
Provides a human-readable at-a-glance quality report covering:
    Overall Score, Character, Glossary, Scene, Narrative, Style,
    Regression, Trend, Suggestion.

Offline. Zero external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DashboardSlot:
    extractor_name: str
    display_name: str
    score: float
    grade: str
    total_cases: int = 0
    passed_cases: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    ece: float = 0.0
    missing_rate: float = 0.0
    hallucination_rate: float = 0.0
    schema_pass: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "extractor": self.extractor_name,
            "display_name": self.display_name,
            "score": round(self.score, 4),
            "grade": self.grade,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "ece": round(self.ece, 4),
            "missing_rate": round(self.missing_rate, 4),
            "hallucination_rate": round(self.hallucination_rate, 4),
            "schema_pass_rate": round(self.schema_pass, 4),
            "cases": {"total": self.total_cases, "passed": self.passed_cases},
        }


@dataclass
class DashboardModel:
    overall_score: float = 0.0
    overall_grade: str = "F"
    slots: List[DashboardSlot] = field(default_factory=list)
    regression_status: str = "N/A"
    regression_details: List[Dict[str, Any]] = field(default_factory=list)
    trend: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 4),
            "overall_grade": self.overall_grade,
            "extractors": [s.to_dict() for s in self.slots],
            "regression_status": self.regression_status,
            "regression_details": self.regression_details,
            "trend": dict(self.trend),
            "suggestions": list(self.suggestions),
            "metadata": dict(self.metadata),
            "generated_at": self.generated_at,
        }

    def to_json(self, indent: int = 2) -> str:
        import json
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_markdown(self) -> str:
        lines = [
            "# NTPE Knowledge Benchmark Dashboard",
            "",
            f"**Generated**: `{self.generated_at}`",
            "",
            "---",
            "",
            "## Overall Score",
            "",
        ]

        score_pct = self.overall_score * 100
        lines.append(f"**Score**: {score_pct:.2f}%")
        lines.append(f"**Grade**: **{self.overall_grade}**")
        lines.append("")

        lines.extend([
            "---",
            "",
            "## Per-Extractor Scores",
            "",
            "| Extractor | Score | Grade | F1 | Precision | Recall | ECE |",
            "|-----------|-------|-------|----|-----------|--------|-----|",
        ])

        for slot in self.slots:
            lines.append(
                f"| {slot.display_name} | {slot.score:.4f} | {slot.grade} | "
                f"{slot.f1:.4f} | {slot.precision:.4f} | {slot.recall:.4f} | {slot.ece:.4f} |"
            )
        lines.append("")

        if self.regression_details:
            lines.extend([
                "---",
                "",
                "## Regression Check",
                "",
            ])
            lines.append(f"**Status**: {self.regression_status}")
            lines.append("")
            lines.append("| Extractor | Baseline F1 | Current F1 | Delta | Status |")
            lines.append("|-----------|-------------|------------|-------|--------|")
            for d in self.regression_details:
                status_icon = "PASS" if d.get("status") == "pass" else "FAIL"
                lines.append(
                    f"| {d.get('extractor', '?')} | {d.get('baseline_f1', 0):.4f} | "
                    f"{d.get('current_f1', 0):.4f} | {d.get('delta', 0):+.4f} | {status_icon} |"
                )
            lines.append("")

        if self.trend:
            lines.extend([
                "---",
                "",
                "## Trend",
                "",
            ])
            for extractor_name, direction in self.trend.items():
                lines.append(f"- **{extractor_name}**: {direction}")
            lines.append("")

        if self.suggestions:
            lines.extend([
                "---",
                "",
                "## Suggestions",
                "",
            ])
            for idx, s in enumerate(self.suggestions, 1):
                lines.append(f"{idx}. {s}")
            lines.append("")

        if self.metadata:
            lines.extend([
                "---",
                "",
                "## Metadata",
                "",
            ])
            for key, val in self.metadata.items():
                lines.append(f"- **{key}**: {val}")
            lines.append("")

        lines.extend([
            "---",
            "",
            f"*Generated: {self.generated_at}*",
            "*NTPE Knowledge Benchmark Runner (RM-5.8.5)*",
        ])

        return "\n".join(lines)


EXTRACTOR_DISPLAY_NAMES: Dict[str, str] = {
    "character": "Character",
    "glossary": "Glossary",
    "scene": "Scene",
    "narrative": "Narrative",
    "style": "Style",
}


class DashboardGenerator:
    """Generates the benchmark quality dashboard."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("benchmarks/results/dashboard")

    def build_from_scorecard(
        self,
        overall_scorecard: Dict[str, Any],
        regression_check: Optional[Dict[str, Any]] = None,
        analysis_overall_summary: Optional[Dict[str, Any]] = None,
        trend_data: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
    ) -> DashboardModel:
        overall = overall_scorecard.get("overall", {})
        overall_score = overall.get("overall_score", 0.0)
        overall_grade = overall.get("grade", "F")

        slots: List[DashboardSlot] = []
        extractor_scores = overall.get("extractor_scores", {})
        summary_ext = overall_scorecard.get("summary", {})
        extractors_details = overall_scorecard.get("extractors", {})

        for ext_name, ext_sc in extractor_scores.items():
            ms = ext_sc.get("metric_scores", {})
            slot = DashboardSlot(
                extractor_name=ext_name,
                display_name=EXTRACTOR_DISPLAY_NAMES.get(ext_name, ext_name.capitalize()),
                score=ext_sc.get("extractor_score", 0.0),
                grade=_compute_grade(ext_sc.get("extractor_score", 0.0)),
                precision=ms.get("precision", {}).get("value", 0.0) if isinstance(ms.get("precision"), dict) else 0.0,
                recall=ms.get("recall", {}).get("value", 0.0) if isinstance(ms.get("recall"), dict) else 0.0,
                f1=ms.get("f1_score", {}).get("value", 0.0) if isinstance(ms.get("f1_score"), dict) else 0.0,
                ece=ms.get("ece", {}).get("value", 0.0) if isinstance(ms.get("ece"), dict) else 0.0,
                missing_rate=ms.get("missing_rate", {}).get("value", 0.0) if isinstance(ms.get("missing_rate"), dict) else 0.0,
                hallucination_rate=ms.get("hallucination_rate", {}).get("value", 0.0) if isinstance(ms.get("hallucination_rate"), dict) else 0.0,
                schema_pass=ms.get("schema_pass_rate", {}).get("value", 0.0) if isinstance(ms.get("schema_pass_rate"), dict) else 0.0,
            )
            ext_detail = extractors_details.get(ext_name, {})
            ext_summary = ext_detail.get("summary", {})
            slot.total_cases = ext_summary.get("total_extractors", 0)
            slot.passed_cases = ext_summary.get("successful_extractors", 0)
            slots.append(slot)

        regression_status = "No Check"
        regression_details: List[Dict[str, Any]] = []
        if regression_check:
            regression_status = regression_check.get("result", "No Check")
            regression_details = regression_check.get("details", [])

        sug_list: List[str] = []
        if analysis_overall_summary:
            for s_item in analysis_overall_summary.get("suggestions", []):
                if isinstance(s_item, dict):
                    sug_list.append(s_item.get("suggestion", ""))
                elif isinstance(s_item, str):
                    sug_list.append(s_item)

        trend: Dict[str, Any] = trend_data or {}
        metadata = overall_scorecard.get("metadata", {})

        return DashboardModel(
            overall_score=overall_score,
            overall_grade=overall_grade,
            slots=slots,
            regression_status=regression_status,
            regression_details=regression_details,
            trend=trend,
            suggestions=sug_list,
            metadata=metadata,
        )

    def write_dashboard(self, dashboard: DashboardModel) -> Dict[str, Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        md_path = self.output_dir / "dashboard.md"
        md_path.write_text(dashboard.to_markdown(), encoding="utf-8")

        json_path = self.output_dir / "dashboard.json"
        json_path.write_text(dashboard.to_json(), encoding="utf-8")

        return {"markdown": md_path, "json": json_path}


def _compute_grade(score: float) -> str:
    if score >= 0.95:
        return "A+"
    elif score >= 0.90:
        return "A"
    elif score >= 0.80:
        return "B"
    elif score >= 0.70:
        return "C"
    return "F"


def create_dashboard_generator() -> DashboardGenerator:
    return DashboardGenerator()