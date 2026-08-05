"""
Runtime Adapter (RM-5.9.1)

Bridges Translation Runtime output into the Knowledge Benchmark system.
Execution flow:

    Translation Output
          |
          v
    Knowledge Extraction (offline)
          |
          v
    Benchmark Scorer
          |
          v
    Regression Gate -> Release Gate
          |
          v
    Quality Decision

Zero provider API calls. Zero network requests.
Does not modify Translation Engine core.
Read-only observer pattern.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.knowledge_benchmark.models import (
    EntityType,
    DifficultyTier,
    BenchmarkMetadata,
)
from core.knowledge_benchmark.comparison import ComparisonEngine, ComparisonConfig
from core.knowledge_benchmark.regression_gate import (
    RegressionGate,
    create_regression_gate,
)
from core.knowledge_benchmark.release_gate import (
    ReleaseGate,
    create_release_gate,
)
from core.knowledge_benchmark.baseline.manager import create_baseline_manager

from .models import (
    QualityDecision,
    QualityStatus,
    QualityScorecard,
    TranslationInput,
    KnowledgeExtractionOutput,
    GateInput,
)

_EXTRACTOR_ENTITY_TYPE: Dict[str, EntityType] = {
    "character": EntityType.CHARACTER,
    "glossary": EntityType.GLOSSARY,
    "scene": EntityType.SCENE,
    "narrative": EntityType.NARRATIVE,
    "style": EntityType.STYLE,
}


class RuntimeAdapter:
    """Quality Observer adapter for runtime translation output.

    Receives translation output and extracted knowledge, then:
    1. Compares extracted knowledge against golden reference
    2. Scores via BenchmarkScorer
    3. Runs Regression Gate against active baseline
    4. Runs Release Gate
    5. Produces Quality Decision
    """

    def __init__(
        self,
        regression_gate: Optional[RegressionGate] = None,
        release_gate: Optional[ReleaseGate] = None,
        comparison_engine: Optional[ComparisonEngine] = None,
    ):
        self._regression_gate = regression_gate or create_regression_gate()
        self._release_gate = release_gate or create_release_gate()
        self._comparison_engine = comparison_engine or ComparisonEngine(ComparisonConfig())
        self._baseline_manager = create_baseline_manager()

    def evaluate(
        self,
        translation: TranslationInput,
        extraction: KnowledgeExtractionOutput,
        golden_entities: List[dict],
        extractor_type: str = "character",
    ) -> QualityDecision:
        entity_type = _EXTRACTOR_ENTITY_TYPE.get(extractor_type, EntityType.CHARACTER)

        comparison = self._comparison_engine.create_comparison(
            extractor_type=entity_type,
            golden_entities=golden_entities,
            predicted_entities=extraction.extracted_entities,
            difficulty_tier=DifficultyTier.EASY,
            source_text=translation.source_text,
            metadata={"adapter": "RM-5.9.1", "extractor": extractor_type},
        )

        metadata = BenchmarkMetadata(
            benchmark_id=f"rt_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            benchmark_version="RM-5.9.1",
            environment="runtime-check",
        )

        scorecard = self._comparison_engine.generate_scorecard([comparison], metadata)
        scorecard_data = scorecard.to_dict()

        gate_input = self._build_gate_input(scorecard_data, extractor_type)
        regression_report_raw = gate_input.regression_gate_report
        baseline_score = gate_input.baseline_score

        release_result = self._release_gate.evaluate(
            overall_scorecard=scorecard_data,
            regression_gate_report=regression_report_raw,
            baseline_score=baseline_score,
        )

        overall = scorecard_data.get("overall", {})
        extractor_scores = overall.get("extractor_scores", {})
        es = extractor_scores.get(entity_type.value, {})

        metric_scores = es.get("metric_scores", {})
        precision = self._extract_metric(metric_scores, "precision")
        recall = self._extract_metric(metric_scores, "recall")
        f1 = self._extract_metric(metric_scores, "f1_score")
        ece = self._extract_metric(metric_scores, "ece")

        qs = QualityScorecard(
            precision=float(precision),
            recall=float(recall),
            f1=float(f1),
            ece=float(ece),
            overall_score=float(overall.get("overall_score", 0.0)),
            grade=str(overall.get("grade", "F")),
        )

        reason: List[str] = []
        recommendations: List[str] = list(release_result.recommendations)

        if release_result.decision.value == "ALLOW":
            status = QualityStatus.PASS
            if release_result.reason and release_result.reason != "All checks passed":
                reason.append(release_result.reason)
        else:
            status = QualityStatus.RETRY_REQUIRED
            reason.append(release_result.reason)

        if regression_report_raw:
            try:
                overall_status = regression_report_raw.get("overall_status", "PASS")
                if overall_status == "WARNING":
                    status = QualityStatus.WARNING
                    reason.append("Regression gate has warnings")
            except (AttributeError, TypeError):
                pass

        return QualityDecision(
            status=status,
            scorecard=qs,
            reason=reason,
            recommendations=recommendations,
            regression_status=(
                regression_report_raw.get("overall_status", "UNKNOWN")
                if isinstance(regression_report_raw, dict)
                else "UNKNOWN"
            ),
            release_decision=release_result.decision.value,
            metadata={
                "adapter": "RM-5.9.1",
                "mode": "offline",
                "provider_requests": 0,
                "network_requests": 0,
                "translation_engine_modified": False,
            },
        )

    @staticmethod
    def _extract_metric(metric_scores: dict, metric_name: str) -> float:
        val = metric_scores.get(metric_name, 0.0)
        if isinstance(val, dict):
            return float(val.get("value", 0.0))
        return float(val)

    def _build_gate_input(
        self,
        scorecard_data: Dict[str, Any],
        extractor_type: str,
    ) -> GateInput:
        regression_report = None
        baseline_score = None

        try:
            baseline = self._baseline_manager.load_baseline()
            if baseline:
                baseline_score = baseline.overall_score

                current_scores: dict = {}
                overall_sc = scorecard_data.get("overall", {})
                for ext_name, ext_sc in overall_sc.get("extractor_scores", {}).items():
                    current_scores[ext_name] = {}
                    ms = ext_sc.get("metric_scores", {})
                    for metric, m_val in ms.items():
                        current_scores[ext_name][metric] = (
                            m_val.get("value", 0.0) if isinstance(m_val, dict) else float(m_val)
                        )

                baseline_scores: dict = {}
                for snapshot in baseline.metric_snapshots:
                    ext = snapshot.extractor_type
                    if ext not in baseline_scores:
                        baseline_scores[ext] = {}
                    baseline_scores[ext][snapshot.metric_name] = snapshot.score

                regression_report = self._regression_gate.evaluate(
                    current_scores, baseline_scores
                )
        except Exception:
            pass

        return GateInput(
            scorecard=scorecard_data,
            regression_gate_report=(
                regression_report.to_dict() if regression_report is not None else None
            ),
            baseline_score=baseline_score,
        )


def create_runtime_adapter() -> RuntimeAdapter:
    return RuntimeAdapter()