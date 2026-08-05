"""
Statistics Engine (RM-5.8.4)

Computes per-extractor summary statistics from benchmark comparison data:
Precision, Recall, F1, Confidence, ECE, Top 5 Failures, Top 5 Successes.

Fully offline. Deterministic. No external dependencies.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from ..models import (
    EntityType,
    ExtractionComparison,
    EntityMatchResult,
)
from .models import ExtractorStatistics


class StatisticsEngine:
    """Computes per-extractor benchmark statistics."""

    def compute_all(
        self,
        comparisons_by_extractor: Dict[str, List[ExtractionComparison]],
    ) -> Dict[str, ExtractorStatistics]:
        results: Dict[str, ExtractorStatistics] = {}
        for extractor_name, comparisons in comparisons_by_extractor.items():
            stats = self.compute_extractor(extractor_name, comparisons)
            results[extractor_name] = stats
        return results

    def compute_extractor(
        self,
        extractor_name: str,
        comparisons: List[ExtractionComparison],
    ) -> ExtractorStatistics:
        stats = ExtractorStatistics(extractor_type=extractor_name)

        all_matches: List[EntityMatchResult] = []
        all_missing: List[Dict[str, Any]] = []
        all_hallucinated: List[Dict[str, Any]] = []
        all_duplicates: List[Dict[str, Any]] = []

        for comp in comparisons:
            all_matches.extend(comp.matches)
            all_missing.extend(comp.missing_entities)
            all_hallucinated.extend(comp.hallucinated_entities)
            all_duplicates.extend(comp.duplicate_entities)

        tp_count = sum(1 for m in all_matches if m.matched)
        fp_count = sum(1 for m in all_matches if not m.matched and m.predicted_entity_id)
        fn_count = sum(1 for m in all_matches if not m.matched and m.golden_entity_id)

        total_predicted = tp_count + fp_count
        total_golden = tp_count + fn_count

        stats.precision = tp_count / total_predicted if total_predicted > 0 else 0.0
        stats.recall = tp_count / total_golden if total_golden > 0 else 0.0
        stats.f1 = (
            2 * (stats.precision * stats.recall) / (stats.precision + stats.recall)
            if (stats.precision + stats.recall) > 0 else 0.0
        )

        confidences = [m.confidence_predicted for m in all_matches if m.predicted_entity_id]
        stats.confidence = sum(confidences) / len(confidences) if confidences else 0.0
        stats.ece = self._compute_ece(all_matches)

        stats.top5_failure, stats.top5_success = self._topify_worst_best(
            stats, all_matches, all_missing, all_hallucinated, all_duplicates
        )

        return stats

    @staticmethod
    def _compute_ece(matches: List[EntityMatchResult]) -> float:
        num_bins = 10
        bins = [{"count": 0, "correct": 0, "total_conf": 0.0} for _ in range(num_bins)]

        total_samples = 0
        for match in matches:
            if not match.predicted_entity_id:
                continue
            confidence = match.confidence_predicted
            is_correct = match.matched
            bin_idx = min(int(confidence * num_bins), num_bins - 1)
            b = bins[bin_idx]
            b["count"] += 1
            b["total_conf"] += confidence
            if is_correct:
                b["correct"] += 1
            total_samples += 1

        if total_samples == 0:
            return 0.0

        ece = 0.0
        for b in bins:
            if b["count"] > 0:
                acc = b["correct"] / b["count"]
                avg_conf = b["total_conf"] / b["count"]
                weight = b["count"] / total_samples
                ece += abs(acc - avg_conf) * weight
        return round(ece, 4)

    @staticmethod
    def _topify_worst_best(
        stats: ExtractorStatistics,
        matches: List[EntityMatchResult],
        missing: List[Dict[str, Any]],
        hallucinated: List[Dict[str, Any]],
        duplicates: List[Dict[str, Any]],
    ) -> Tuple[List[str], List[str]]:
        top5_failure: List[str] = []
        top5_success: List[str] = []

        failure_candidates: List[Tuple[str, float, str]] = []

        for m in missing:
            eid = m.get("id", m.get("entity_id", "?"))
            conf = float(m.get("confidence", 0.0))
            failure_candidates.append(("missing_entity", conf, f"Missing {eid} (conf={conf:.2f})"))

        for h in hallucinated:
            eid = h.get("id", h.get("entity_id", "?"))
            conf = float(h.get("confidence", 0.0))
            failure_candidates.append(("hallucinated", conf, f"Hallucination {eid} (conf={conf:.2f})"))

        for d in duplicates:
            eid = d.get("id", d.get("entity_id", "?"))
            failure_candidates.append(("duplicate", 0.0, f"Duplicate {eid}"))

        for match in matches:
            if not match.matched and match.golden_entity_id and match.predicted_entity_id:
                failure_candidates.append(
                    ("unmatched",
                     match.similarity_score,
                     f"Unmatched {match.golden_entity_id}/{match.predicted_entity_id} (sim={match.similarity_score:.2f})")
                )

        failure_candidates.sort(key=lambda x: (x[0] != "missing_entity", x[1]))
        top5_failure = [f[2] for f in failure_candidates[:5]]

        success_candidates = []
        for match in matches:
            if match.matched and match.similarity_score >= 0.9:
                success_candidates.append(
                    (match.similarity_score,
                     f"Exact match {match.golden_entity_id} (sim={match.similarity_score:.2f})")
                )
        success_candidates.sort(key=lambda x: -x[0])
        top5_success = [s[1] for s in success_candidates[:5]]

        if not top5_failure:
            top5_failure.append("No failures detected")
        if not top5_success:
            top5_success.append("No exact matches detected")

        return top5_failure, top5_success


def create_statistics_engine() -> StatisticsEngine:
    return StatisticsEngine()