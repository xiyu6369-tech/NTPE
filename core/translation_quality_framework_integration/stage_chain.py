from __future__ import annotations

STAGE_CHAIN = ("11.1", "11.2", "11.3", "11.4", "11.5", "11.6")
STAGE_NAMES = {
    "11.1": "defects",
    "11.2": "metrics",
    "11.3": "review_artifacts",
    "11.4": "improvement_plans",
    "11.5": "human_review_decision",
    "11.6": "golden_corpus_governance",
}
STAGE_PIPELINE_STATUS = {
    "11.1": "recorded",
    "11.2": "calculated",
    "11.3": "created",
    "11.4": "not_applied",
    "11.5": "not_applied",
    "11.6": "not_applied",
}


def validate_stage_chain(stages: tuple[str, ...] | list[str]) -> bool:
    chain = tuple(stages)
    if chain != STAGE_CHAIN:
        raise ValueError("quality framework stage chain must be exactly 11.1 through 11.6")
    if len(chain) != len(set(chain)):
        raise ValueError("quality framework stage chain contains duplicates")
    return True

