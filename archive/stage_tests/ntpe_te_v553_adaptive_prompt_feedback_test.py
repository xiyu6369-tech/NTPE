from __future__ import annotations

import os

from core.prompt_compiler.adaptive_feedback import build_adaptive_feedback
from lts.txt_translation_runtime import build_qa_retry_user_prompt


def main() -> int:
    qa = {
        "unified_quality_report": {
            "merged_issues": [
                {
                    "code": "SEMANTIC_DUPLICATE_PARAGRAPH",
                    "severity": "high",
                    "retry_required": True,
                    "message": "duplicate",
                },
                {
                    "code": "SIMPLIFIED_CHINESE",
                    "severity": "medium",
                    "retry_required": False,
                    "message": "normalize",
                },
            ]
        },
        "issues": [],
    }
    feedback = build_adaptive_feedback(qa)
    prompt = build_qa_retry_user_prompt("【Korean】\n원문", qa, 2)
    assert feedback.codes == ("SEMANTIC_DUPLICATE_PARAGRAPH",)
    assert "不得換句話重述" in prompt
    assert "Previous 僅供語境承接" in prompt
    assert "SIMPLIFIED_CHINESE" not in prompt

    omission = {
        "unified_quality_report": {
            "merged_issues": [{
                "code": "TOO_SHORT",
                "severity": "high",
                "retry_required": True,
            }]
        }
    }
    omission_prompt = build_qa_retry_user_prompt("Translate.", omission, 2)
    assert "逐句覆蓋原文全部資訊" in omission_prompt

    old = os.environ.get("NTPE_ADAPTIVE_PROMPT_FEEDBACK")
    try:
        os.environ["NTPE_ADAPTIVE_PROMPT_FEEDBACK"] = "0"
        fallback = build_qa_retry_user_prompt("Translate.", omission, 2)
        assert "Adaptive Prompt Feedback" not in fallback
        assert "NTPE 自動重試指令" in fallback
    finally:
        if old is None:
            os.environ.pop("NTPE_ADAPTIVE_PROMPT_FEEDBACK", None)
        else:
            os.environ["NTPE_ADAPTIVE_PROMPT_FEEDBACK"] = old

    print("TE v5.5.3 Adaptive Prompt Feedback Test")
    print("=======================================")
    print("Blocking issues mapped to directives PASS")
    print("Nonblocking issues excluded          PASS")
    print("Omission feedback targeted           PASS")
    print("Rollback switch compatible           PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
