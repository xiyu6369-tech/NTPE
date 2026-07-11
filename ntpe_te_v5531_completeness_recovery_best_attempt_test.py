from __future__ import annotations

from core.prompt_compiler.adaptive_feedback import build_adaptive_feedback, render_adaptive_feedback_block
from core.translation_quality_v5.best_attempt import AttemptCandidate, select_best_attempt, selection_metadata


def _qa(decision: str, score: int, code: str, *, severity: str = "high", retry: bool = True) -> dict:
    issue = {
        "code": code,
        "severity": severity,
        "retry_required": retry,
        "message": code,
        "evidence": {
            "source_paragraphs": 6,
            "translated_paragraphs": 2,
            "source_sentences": 8,
            "translated_sentences": 3,
            "length_ratio": 0.41,
        },
    }
    unified = {
        "decision": decision,
        "score": score,
        "merged_issues": [issue],
    }
    return {
        "decision": decision,
        "score": score,
        "passed": decision in {"accepted", "accepted_with_warnings"},
        "issues": [issue],
        "unified_quality_report": unified,
    }


def main() -> int:
    first_qa = _qa("retry_required", 80, "PARAGRAPH_OMISSION_SUSPECTED")
    feedback = build_adaptive_feedback(first_qa)
    block = render_adaptive_feedback_block(feedback, 2)
    assert feedback.codes == ("PARAGRAPH_OMISSION_SUSPECTED",)
    assert "原文段落 6" in block
    assert "前次譯文段落 2" in block
    assert "原文句數 8" in block
    assert "前次譯文句數 3" in block
    assert "長度比 0.41" in block
    assert "只補回遺漏資訊" in block

    second_qa = _qa("retry_required", 70, "PARAGRAPH_OMISSION_SUSPECTED")
    first = AttemptCandidate(1, "較完整的第一版譯文。", first_qa, None, {"status": "success", "qa_attempt": 1})
    second = AttemptCandidate(2, "退化的第二版。", second_qa, None, {"status": "success", "qa_attempt": 2})
    selected = select_best_attempt([first, second])
    assert selected is first
    meta = selection_metadata([first, second], selected)
    assert meta["selected_qa_attempt"] == 1
    assert meta["candidate_count"] == 2

    accepted_qa = {
        "decision": "accepted_with_warnings",
        "score": 90,
        "passed": True,
        "issues": [{"code": "PARAGRAPH_STRUCTURE_MERGED", "severity": "medium", "retry_required": False}],
        "unified_quality_report": {
            "decision": "accepted_with_warnings",
            "score": 90,
            "merged_issues": [{"code": "PARAGRAPH_STRUCTURE_MERGED", "severity": "medium", "retry_required": False}],
        },
    }
    third = AttemptCandidate(2, "已修復並可放行的第二版。", accepted_qa, None, {"status": "success", "qa_attempt": 2})
    assert select_best_attempt([first, third]) is third

    print("TE v5.5.3.1 Completeness Recovery Feedback & Best Attempt Selection")
    print("=================================================================")
    print("Coverage metrics injected into feedback PASS")
    print("Recovery directives remain conservative PASS")
    print("Worse retry cannot replace better attempt PASS")
    print("Accepted retry outranks failed attempt PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
