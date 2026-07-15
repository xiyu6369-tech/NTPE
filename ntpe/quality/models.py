"""Immutable, non-serialized views over frozen quality-domain models."""

from __future__ import annotations

from dataclasses import dataclass

from core.translation_prompt_improvement_planner import PromptImprovementPlan
from core.translation_quality_defects import TranslationDefect
from core.translation_quality_metrics import QualityMetric
from core.translation_quality_review_artifacts import StructuredReview
from core.translation_quality_review_decision import HumanReviewDecision


@dataclass(frozen=True, slots=True)
class QualityAssessment:
    defects: tuple[TranslationDefect, ...]
    metrics: tuple[QualityMetric, ...]
    blocking_defect_count: int
    overall_score: float
    quality_pass: bool
    insufficient_evidence_dimensions: tuple[str, ...]
    source_references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class QualityReview:
    review: StructuredReview
    improvement_plans: tuple[PromptImprovementPlan, ...]
    human_decision: HumanReviewDecision | None
    plans_applied: bool
    decision_applied: bool
    human_approval_required: bool
    source_references: tuple[str, ...]
    corpus_approval_granted: bool = False

