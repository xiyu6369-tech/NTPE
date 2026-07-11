from __future__ import annotations

from core.prompt_compiler.adaptive_feedback import ADAPTIVE_FEEDBACK_VERSION, build_adaptive_feedback
from lts.txt_translation_runtime import build_qa_retry_user_prompt


def test_adaptive_feedback_uses_unified_blocking_issues_only() -> None:
    qa = {
        "unified_quality_report": {
            "merged_issues": [
                {"code": "HALLUCINATION", "severity": "high", "retry_required": True},
                {"code": "NATURALNESS_GUARD", "severity": "medium", "retry_required": False},
            ]
        }
    }
    feedback = build_adaptive_feedback(qa)
    prompt = build_qa_retry_user_prompt("SOURCE", qa, 2)
    assert ADAPTIVE_FEEDBACK_VERSION.startswith("5.5.3")
    assert feedback.codes == ("HALLUCINATION",)
    assert "不得創造原文不存在的專名" in prompt
    assert "自然的繁體中文小說句法" not in prompt
