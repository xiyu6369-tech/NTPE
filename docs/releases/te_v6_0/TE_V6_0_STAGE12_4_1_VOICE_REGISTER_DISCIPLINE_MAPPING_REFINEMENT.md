# TE v6.0 Stage 12.4.1 — Voice/Register Discipline Mapping Refinement

Stage 12.4.1 replaces the broad `PRESERVE_PARAGRAPH_INTENT` fallback for voice and register findings with seven specific, traceable Translation Discipline rules. The rules live in the unified registry with the `adaptive_retry` phase and are feedback-only/default-inactive, so Adaptive Feedback can resolve them without changing the frozen active/generation rule count, adding a second prompt policy, or changing existing generation prompt text.

`UNSUPPORTED_EMOTIONAL_AMPLIFICATION` continues to map to `NO_ADDED_PSYCHOLOGY`. All Stage 12.4 findings remain warnings: non-blocking, not locally repairable, and `retry_required=false`. They remain outside Quality score inputs and cannot independently change the Unified decision or initiate a Provider request.

No Provider client, HTTP path, NVIDIA API call, semantic local rewrite, or Stage 12.5 behavior is introduced.
