from __future__ import annotations

from core.translation_quality_defects import TranslationDefect, validate_defects
from core.translation_quality_metrics import QualityMetric

from .mapping import DEFECT_PLAN_MAPPING
from .model import PromptImprovementPlan
from .risk import RISK_DESCRIPTIONS
from .validator import validate_plans

PLAN_CONTENT = {
    "TQ-DEF-A": ("The reviewed 인간 phrase became the unnatural noun 人間.", "Propose a context-sensitive person-noun check in naturalness guidance.", "Reduce literal lexical substitutions while retaining source meaning."),
    "TQ-DEF-B": ("Reviewed transport and island-access information was omitted.", "Propose a clause-coverage checkpoint for explicit scene logistics.", "Make omission evidence visible before accepting a translation."),
    "TQ-DEF-C": ("Anger-induced bedrest was shifted into wailing.", "Propose an action-state fidelity check for emotion and physical consequence.", "Reduce action and emotional-state semantic drift."),
    "TQ-DEF-D": ("The concrete loss or shortening of a holiday was weakened.", "Propose preserving explicit consequence and degree in fidelity guidance.", "Retain semantic precision without prescribing a final translation."),
    "TQ-DEF-E": ("遠國 and the surrounding order read as translated syntax.", "Propose a narrative-order review for stiff location constructions.", "Improve narrative Chinese while preserving setting and tone."),
    "TQ-DEF-F": ("一周 conflicts with the reviewed Traditional Chinese style convention.", "Propose a non-destructive Traditional Chinese typography consistency check.", "Improve orthographic consistency without changing meaning."),
}


def create_prompt_improvement_plans(defects: tuple[TranslationDefect, ...], metrics: tuple[QualityMetric, ...]) -> tuple[PromptImprovementPlan, ...]:
    defects = validate_defects(defects)
    metric_ids = {defect_id for metric in metrics for defect_id in metric.related_defect_ids}
    plans = []
    for index, defect in enumerate(defects, 1):
        if defect.defect_id not in metric_ids or defect.defect_id not in DEFECT_PLAN_MAPPING:
            continue
        section, risk_level, priority = DEFECT_PLAN_MAPPING[defect.defect_id]
        problem, change, benefit = PLAN_CONTENT[defect.defect_id]
        plans.append(PromptImprovementPlan(f"TQ-PLAN-{index:02d}", (defect.defect_id,), section, problem, change, benefit, RISK_DESCRIPTIONS[risk_level], risk_level, priority, "Human review plus a future isolated regression corpus comparison; no result is claimed in this stage."))
    return validate_plans(plans)
