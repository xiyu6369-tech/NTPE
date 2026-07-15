# TE v7.2 Stage 12.1 — Evidence-Based Prompt Quality Candidate

## Outcome

Stage 12.1 adds one small, reversible literary prompt candidate derived from the human-reviewed Stage 10.10.1 evidence and the frozen Stage 11.1/11.4 defect and plan artifacts. It does not add a framework, replace the production prompt, or claim that translation quality improved.

## Change

`core.literary_prompt_quality_candidate_v72.build_literary_prompt` delegates to the frozen `core.literary.LiteraryPromptBuilder`. With `candidate_enabled=false` (the default), it returns the baseline user prompt unchanged. With `candidate_enabled=true`, it inserts one policy block immediately before the existing narrative context. The system prompt, source, context, glossary, output instruction and compiler behavior remain unchanged.

The opt-in feature name is `--quality-candidate-v72`; the programmatic configuration is `candidate_enabled=true`. Rollback is immediate by setting it to `false`. No existing CLI or production runtime was modified to consume the flag.

## Candidate policy

The compact policy covers evidence-backed fidelity, ambiguity, completeness, natural Traditional Chinese narrative order, period/context-aware wording, dialogue and character voice, and no unsupported full-name completion. It does not require Taiwan-specific vocabulary. Only one candidate is included so a later same-source A/B review changes one variable.

The deterministic delta is 263 characters and 109 estimated multilingual tokens, within the 120-token limit. Source, context and glossary budgets are not reduced; max output tokens and chunk size are unchanged.

## Validation and execution boundary

Offline verification includes the Stage 12.1 root test, focused integration test, static coverage of all six evidence categories, Stage 11 freeze anchors and TE v6 regression anchors. Static policy coverage does not prove better translation output.

The provider execution package fixes the Stage 10.10.1 source unit (`Golden_Set:1`), model, timeout, single-attempt retry setting, output budget and chunk size. It plans one baseline plus one candidate request, but Stage 12.1 did not execute either request. No network request was sent and no new translation was generated.

`quality_baseline` and `quality_candidate_result` remain unset. Translation quality improvement is not verified, the candidate is `prepared_not_validated`, and publication-grade quality is not claimed.

## Next step

Do not start Stage 12.2 from this delivery. After separate explicit real-provider authorization and review of the prompt-adapter hookup, run the same frozen source unit for baseline and candidate, preserve all request artifacts and SHA-256 values, and have a human reviewer complete the supplied A/B template. The candidate advances only if every documented quality gate passes; otherwise it remains `rejected_or_needs_revision`.
