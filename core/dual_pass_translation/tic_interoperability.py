from __future__ import annotations
from core.translation_intelligence_corpus.offline_quality_gate import evaluate_translation_candidate
def evaluate_tic_batch7_candidate(*,source_text,translation_text,regression_id):
    result=evaluate_translation_candidate(source_text=source_text,translation_text=translation_text,applicable_regression_ids=(regression_id,));return {"status":result.gate_status,"allowed":result.quality_candidate_allowed,"regression_safe":result.regression_safe,"reasons":result.failure_reasons}
