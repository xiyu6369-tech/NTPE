"""Benchmark Runner (RM-5.8.3)

Main orchestration engine for the offline Knowledge Benchmark pipeline.

Pipeline:
    Golden Dataset -> Knowledge Extractor -> Comparison -> Metrics -> Scorecard -> Regression Report

Completely offline. Zero provider/NTP API calls. Zero network requests.
Read-only: does not modify Runtime, Translation Package, Knowledge Package, or Provider.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from core.knowledge_benchmark.models import (
    BenchmarkMetadata,
    EntityType,
    DifficultyTier,
    MetricName,
    OverallScore,
    ExtractorScore,
)
from core.knowledge_benchmark.comparison import (
    ComparisonEngine,
    ComparisonConfig,
)

from .loader import BenchmarkCorpusLoader
from .executor import ExtractionExecutor, ExecutionResult, EXTRACTOR_DISPLAY_NAMES
from .report_writer import ReportWriter


EXTRACTOR_ENTITY_TYPE: Dict[str, EntityType] = {
    "character": EntityType.CHARACTER,
    "glossary": EntityType.GLOSSARY,
    "scene": EntityType.SCENE,
    "narrative": EntityType.NARRATIVE,
    "style": EntityType.STYLE,
}

DIFFICULTY_MAP: Dict[str, DifficultyTier] = {
    "easy": DifficultyTier.EASY,
    "medium": DifficultyTier.MEDIUM,
    "hard": DifficultyTier.HARD,
}

ALL_EXTRACTORS = ["character", "glossary", "scene", "narrative", "style"]


@dataclass
class RunResult:
    extractor_name: str
    success: bool
    total_cases: int
    passed_cases: int
    comparisons: List = field(default_factory=list)
    extractor_score: Optional[ExtractorScore] = None
    scorecard_data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class Runner:
    """Main offline benchmark runner.

    Pipeline:
        Load Golden Dataset
        -> Execute Extractor per case
        -> Compare against expected entities
        -> Score metrics
        -> Generate scorecard
        -> Check regression vs baseline
        -> Write reports
    """

    def __init__(self, root_path: Optional[Path] = None):
        self.root_path = Path(root_path) if root_path else Path(".")
        self.loader = BenchmarkCorpusLoader(self.root_path)
        self.executor = ExtractionExecutor()
        self.engine = ComparisonEngine(ComparisonConfig())
        self.writer = ReportWriter()
        self.metadata = BenchmarkMetadata(
            benchmark_id=f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            benchmark_version="RM-5.8.3",
            golden_dataset_version="v1.0.0",
            deterministic_seed=42,
        )

    def run_extractor(self, extractor_name: str) -> RunResult:
        if extractor_name not in ALL_EXTRACTORS:
            return RunResult(
                extractor_name=extractor_name,
                success=False,
                total_cases=0,
                passed_cases=0,
                errors=[f"Unknown extractor: {extractor_name}"],
            )

        cases = self.loader.load_extractor(extractor_name)
        if not cases:
            return RunResult(
                extractor_name=extractor_name,
                success=False,
                total_cases=0,
                passed_cases=0,
                errors=["No benchmark cases found"],
            )

        entity_type = EXTRACTOR_ENTITY_TYPE[extractor_name]
        comparisons = []
        errors = []

        for case in cases:
            execution = self.executor.execute(extractor_name, case.source_text)
            if execution.error:
                errors.append(f"[{case.benchmark_id}] {execution.error}")
                continue

            difficulty = DIFFICULTY_MAP.get(case.difficulty, DifficultyTier.EASY)
            golden_entities = case.expected_entities
            predicted_entities = execution.extracted_entities or []

            comparison = self.engine.create_comparison(
                extractor_type=entity_type,
                golden_entities=golden_entities,
                predicted_entities=predicted_entities,
                difficulty_tier=difficulty,
                source_text=case.source_text,
                metadata={"benchmark_id": case.benchmark_id, "tags": case.tags},
            )
            comparisons.append(comparison)

        if not comparisons:
            return RunResult(
                extractor_name=extractor_name,
                success=False,
                total_cases=len(cases),
                passed_cases=0,
                errors=errors,
            )

        scorecard = self.engine.generate_scorecard(comparisons, self.metadata)
        extractor_score = scorecard.overall.extractor_scores.get(entity_type)

        return RunResult(
            extractor_name=extractor_name,
            success=True,
            total_cases=len(cases),
            passed_cases=len(comparisons),
            comparisons=comparisons,
            extractor_score=extractor_score,
            scorecard_data=scorecard.to_dict(),
            errors=errors,
        )

    def run_all(self) -> Dict[str, RunResult]:
        results: Dict[str, RunResult] = {}
        for extractor_name in ALL_EXTRACTORS:
            results[extractor_name] = self.run_extractor(extractor_name)
        return results

    def check_regression(
        self,
        current_results: Dict[str, RunResult],
    ) -> Dict[str, Any]:
        details: List[Dict[str, Any]] = []
        has_regression = False

        for extractor_name, result in current_results.items():
            if result.extractor_score is None:
                continue

            baseline = self.writer.load_baseline(extractor_name)
            if baseline is None:
                continue

            baseline_overall = baseline.get("overall", {})
            baseline_es = baseline_overall.get("extractor_scores", {}).get(extractor_name, {})
            if not baseline_es:
                continue

            current_f1 = self._get_f1_from_score(result.extractor_score)
            baseline_f1 = self._get_f1_from_data(baseline_es)
            if current_f1 is None or baseline_f1 is None:
                continue

            delta = current_f1 - baseline_f1
            threshold = 0.02
            is_regression = delta < -threshold

            entry: Dict[str, Any] = {
                "extractor": extractor_name,
                "baseline_f1": round(baseline_f1, 4),
                "current_f1": round(current_f1, 4),
                "delta": round(delta, 4),
                "threshold": threshold,
                "status": "fail" if is_regression else "pass",
            }

            current_precision = self._get_precision_from_score(result.extractor_score)
            current_recall = self._get_recall_from_score(result.extractor_score)
            current_ece = self._get_ece_from_score(result.extractor_score)

            if current_precision is not None:
                entry["current_precision"] = current_precision
            if current_recall is not None:
                entry["current_recall"] = current_recall
            if current_ece is not None:
                entry["current_ece"] = current_ece

            details.append(entry)
            if is_regression:
                has_regression = True

        return {
            "result": "Regression FAIL" if has_regression else "Regression PASS",
            "regressions_detected": sum(1 for d in details if d.get("status") == "fail"),
            "details": details,
        }

    @staticmethod
    def _get_f1_from_score(es: ExtractorScore) -> Optional[float]:
        if hasattr(es, 'metric_scores') and MetricName.F1_SCORE in es.metric_scores:
            return es.metric_scores[MetricName.F1_SCORE].value
        if es and hasattr(es, 'extractor_score'):
            return es.extractor_score
        return None

    @staticmethod
    def _get_f1_from_data(data: Dict[str, Any]) -> Optional[float]:
        metric_scores = data.get("metric_scores", {})
        f1_data = metric_scores.get("f1_score", {})
        return f1_data.get("value")

    @staticmethod
    def _get_precision_from_score(es: ExtractorScore) -> Optional[float]:
        if hasattr(es, 'metric_scores') and MetricName.PRECISION in es.metric_scores:
            return round(es.metric_scores[MetricName.PRECISION].value, 4)
        return None

    @staticmethod
    def _get_recall_from_score(es: ExtractorScore) -> Optional[float]:
        if hasattr(es, 'metric_scores') and MetricName.RECALL in es.metric_scores:
            return round(es.metric_scores[MetricName.RECALL].value, 4)
        return None

    @staticmethod
    def _get_ece_from_score(es: ExtractorScore) -> Optional[float]:
        if hasattr(es, 'metric_scores') and MetricName.ECE in es.metric_scores:
            return round(es.metric_scores[MetricName.ECE].value, 4)
        return None

    def build_overall_scorecard(
        self,
        results: Dict[str, RunResult],
    ) -> Dict[str, Any]:
        overall = OverallScore()
        for extractor_name, result in results.items():
            if result.extractor_score is not None:
                overall = overall.add_extractor_score(result.extractor_score)
        overall = overall.compute_overall()

        regression_check = self.check_regression(results)

        summary = {
            "total_extractors": len(results),
            "successful_extractors": sum(1 for r in results.values() if r.success),
            "total_cases_ran": sum(r.total_cases for r in results.values()),
            "total_cases_passed": sum(r.passed_cases for r in results.values()),
            "total_errors": sum(len(r.errors) for r in results.values()),
            "regression_result": regression_check.get("result", "UNKNOWN"),
            "regression_count": regression_check.get("regressions_detected", 0),
        }

        return {
            "metadata": self.metadata.to_dict(),
            "overall": overall.to_dict(),
            "regression_check": regression_check,
            "summary": summary,
            "extractors": {
                name: result.scorecard_data
                for name, result in results.items()
            },
        }

    def write_outputs(
        self,
        results: Dict[str, RunResult],
        compare_baseline: bool = False,
    ) -> None:
        for extractor_name, result in results.items():
            if result.success and result.scorecard_data:
                self.writer.write_scorecard(extractor_name, result.scorecard_data)

        overall_data = self.build_overall_scorecard(results)
        self.writer.write_overall_scorecard(overall_data)

        report_md = self._build_report_md(results, overall_data, compare_baseline)
        self.writer.write_report(report_md)

        self.writer.archive_to_history(self.metadata.benchmark_id)

    def _build_report_md(
        self,
        results: Dict[str, RunResult],
        overall_data: Dict[str, Any],
        compare_baseline: bool,
    ) -> str:
        lines = [
            "# Knowledge Benchmark Report",
            "",
            f"**Run ID**: `{self.metadata.benchmark_id}`",
            f"**Timestamp**: `{self.metadata.timestamp}`",
            f"**Framework Version**: `{self.metadata.benchmark_version}`",
            f"**Golden Dataset Version**: `{self.metadata.golden_dataset_version}`",
            "",
            "---",
            "",
            "## Summary",
            "",
        ]

        summary = overall_data.get("summary", {})
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        for key, val in summary.items():
            lines.append(f"| {key} | {val} |")
        lines.append("")

        overall = overall_data.get("overall", {})
        overall_score = overall.get("overall_score", 0.0)
        grade = overall.get("grade", "F")
        lines.append(f"**Overall Score**: {overall_score}")
        lines.append(f"**Grade**: **{grade}**")
        lines.append("")

        lines.extend([
            "---",
            "",
            "## Extractor Results",
            "",
        ])

        for extractor_name in ALL_EXTRACTORS:
            if extractor_name not in results:
                continue
            result = results[extractor_name]
            display_name = EXTRACTOR_DISPLAY_NAMES.get(extractor_name, extractor_name.capitalize())
            lines.append(f"### {display_name}")
            lines.append("")

            if not result.success:
                lines.append("FAILED")
                for err in result.errors:
                    lines.append(f"  - {err}")
                lines.append("")
                continue

            lines.append(f"- Cases: {result.total_cases} total, {result.passed_cases} processed")
            lines.append(f"- Errors: {len(result.errors)}")
            lines.append("")

            if result.extractor_score and hasattr(result.extractor_score, 'metric_scores'):
                ms = result.extractor_score.metric_scores
                lines.append("| Metric | Value | Target | Status |")
                lines.append("|--------|-------|--------|--------|")
                display_metrics = [
                    MetricName.PRECISION, MetricName.RECALL,
                    MetricName.F1_SCORE, MetricName.MISSING_RATE,
                    MetricName.HALLUCINATION_RATE, MetricName.ECE,
                ]
                for metric_name in display_metrics:
                    if metric_name in ms:
                        m = ms[metric_name]
                        status = "PASS" if m.passed else "FAIL"
                        lines.append(
                            f"| {metric_name.value} | {m.value:.4f} | {m.target:.4f} | {status} |"
                        )
                lines.append(f"| **Extractor Score** | **{result.extractor_score.extractor_score:.4f}** | | |")
            lines.append("")

        regression_check = overall_data.get("regression_check", {})
        if regression_check and regression_check.get("details"):
            lines.extend([
                "---",
                "",
                "## Regression Check",
                "",
                "| Extractor | Baseline F1 | Current F1 | Delta | Status |",
                "|-----------|-------------|------------|-------|--------|",
            ])
            for detail in regression_check["details"]:
                status = "PASS" if detail["status"] == "pass" else "FAIL"
                lines.append(
                    f"| {detail['extractor']} | {detail['baseline_f1']:.4f} | {detail['current_f1']:.4f} | {detail['delta']:+.4f} | {status} |"
                )
            lines.append("")
            lines.append(f"**Regression Threshold**: F1 drop > 0.02 (2 percentage points)")
            lines.append(f"**Result**: **{regression_check.get('result', 'UNKNOWN')}**")
            lines.append("")

        lines.extend([
            "---",
            "",
            "*Generated by NTPE Knowledge Benchmark Runner (RM-5.8.3)*",
            "*Offline  Zero provider requests  Zero network requests*",
        ])

        return "\n".join(lines)