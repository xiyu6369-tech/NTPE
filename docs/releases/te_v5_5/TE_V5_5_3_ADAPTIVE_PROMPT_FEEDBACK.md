# TE v5.5.3 Adaptive Prompt Feedback

TE v5.5.3 replaces generic blind QA reruns with issue-directed retry prompts.

## Behavior

- Reads blocking issues from the Unified Quality Gate.
- Maps omission, Hangul residue, terminology, repetition, semantic duplication, and hallucination risks to focused retry directives.
- Excludes nonblocking local-repair warnings from Provider retry feedback.
- Writes adaptive feedback version, issue codes, directive count, and QA attempt into `prompt_runtime.adaptive_feedback`.
- Keeps the existing `build_qa_retry_user_prompt()` string-return API compatible.
- Can be disabled with `NTPE_ADAPTIVE_PROMPT_FEEDBACK=0`.

No Provider, timeout, RPM, backpressure, resume, or Quality Gate behavior is changed.
