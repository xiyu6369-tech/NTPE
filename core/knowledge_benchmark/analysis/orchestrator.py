"""
Analysis Orchestrator (RM-5.8.4)

Central engine that coordinates all analysis modules:
FailureClassifier, StatisticsEngine, RegressionAnalyzer, SuggestionEngine,
TrendAnalyzer, and generates the final AnalysisReport.

Offline. Zero external dependencies. Read-only on Runtime/Translation/Knowledge.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import json
from datetime import datetime, timezone

from ..models import ExtractionComparison
from ..comparison import ComparisonEngine
from .models import (
    FailureSummary,
    RegressionResult,
    Suggestion,
    ExtractorStatistics,
    TrendResult,
    AnalysisReport,
)
from .failure_classifier import FailureClassifier, create_failure_classifier
from .statistics import StatisticsEngine, create_statistics_engine
from .regression_analyzer import RegressionAnalyzer, create_regression_analyzer
from .suggestion_engine import SuggestionEngine, create_suggestion_engine
from .trend_analyzer import TrendAnalyzer, create_trend_analyzer


class Analyzer:
    """Main orchestrator for benchmark analysis.

    Coordinates all five analysis engines in order:
        1. FailureClassification -> FailureSummary
        2. Statistics  -> ExtractorStatistics
        3. Regression -> RegressionResults
        4. Suggestion -> Suggestions
        5. Trend -> Trend Results
        6. Report -> AnalysisReport

    All engines are fully offline and deterministic.
    """

    def __init__(self):
        self.classifier = create_failure_classifier()
        self.statistics = create_statistics_engine()
        self.regression = create_regression_analyzer()
        self.suggestions = create_suggestion_engine()
        self.trend = create_trend_analyzer()

    def analyze(
        self,
        comparisons: List,
        baseline_results: Optional[Dict[str, Dict[str, float]]] = None,
        trend_histories: Optional[Dict[str, List[Dict[str, float]]]] = None,
    ) -> AnalysisReport:
        comparisons_by_extractor: Dict[str, List] = {}
        for comp in comparisons:
            et = comp.extractor_type.value
            comparisons_by_extractor.setdefault(et, []).append(comp)

        failure_summary = self.classifier.build_summary(comparisons)

        stats = self.statistics.compute_all(comparisons_by_extractor)
        current_scores: Dict[str, Dict[str, float]] = {}
        for ext_name, stat in stats.items():
            current_scores[ext_name] = {
                "precision": stat.precision,
                "recall": stat.recall,
                "f1_score": stat.f1,
                "ece": stat.ece,
            }

        regression_results = self.regression.analyze_all(current_scores, baseline_results)

        suggestions = self.suggestions.generate(failure_summary, current_scores)

        trend_results: List[TrendResult] = []
        if trend_histories:
            trend_results = self.trend.analyze_all(trend_histories)
        overall_summary = self._build_overall_summary(
            failure_summary, stats, regression_results, suggestions, trend_results
        )

        return AnalysisReport(
            failure_summary=failure_summary,
            regression_results=regression_results,
            suggestions=suggestions,
            statistics=stats,
            trend_results=trend_results,
            overall_summary=overall_summary,
        )

    def analyze_from_scorecards(
        self,
        scorecards_path: str,
        baseline_path: Optional[str] = None,
    ) -> AnalysisReport:
        scores = self._load_scores(scorecards_path)

        baseline = None
        if baseline_path:
            baseline = self._load_scores(baseline_path)

        regression_results = self.regression.analyze_all(scores, baseline)

        return AnalysisReport(
            regression_results=regression_results,
            overall_summary={
                "source": scores_path,
                "baseline": baseline_path or "none",
                "generated": datetime.now(timezone.utc).isoformat(),
            },
        )

    def write_report(
        self,
        report: AnalysisReport,
        output_dir: str = "benchmarks/results/current",
    ) -> Dict[str, Path]:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        md_path = out_dir / "analysis_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(report.to_markdown())

        json_path = out_dir / "analysis_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        return {"markdown": md_path, "json": json}

    def _build_overall_summary(
        self,
        failure_summary: FailureSummary,
        stats: Dict[str, ExtractorStatistics],
        regression_results: List[RegressionResult],
        suggestions: List[Suggestion],
        trend_results: List[TrendResult],
    ) -> Dict[str, Any]:
        overall_f1 = 0.0
        count = 0
        for st in stats.values():
            overall_f1 += st.f1
            count += 1
        avg_f1 = overall_f1 / count if count > 0 else 0.0

        return {
            "total_failures": failure_summary.total_failures,
            "average_f1": round(avg_f1, 4),
            "total_extractors_analyzed": len(stats),
            "total_suggestions": len(suggestions),
            "total_regression": sum(1 for r in regression_results if r.status != "PASS"),
            "total_trend_analyzed": len(trend_results),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _load_scores(scorecard_path: str) -> Dict[str, Dict[str, float]]:
        scores: Dict[str, Dict[str, float]] = {}
        path = Path(scorecard_path)

        if not path.is_dir():
            return scores

        for json_file in path.glob("*_scorecard.json"):
            extractor_name = json_file.stem.replace("_scorecard", "")
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            scores[extractor_name] = {}
            extractor_data = data.get("extractor_scores", {})
            for et_name, et_sc in extractor_data.items():
                if et_name not in scores:
                    scores[et_name] = {}
                metric_scores = et_sc.get("metric_scores", {})
                for metric_name, ms_data in metric_scores.items():
                    scores[et_name][metric_name] = ms_data.get("value", 0.0)

        return scores


def create_analyzer() -> Analyzer:
    return Analyzer()