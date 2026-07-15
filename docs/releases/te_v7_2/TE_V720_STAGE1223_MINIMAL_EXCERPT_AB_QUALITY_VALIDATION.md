# TE v7.2 Stage 12.2.3 — Minimal-Excerpt Provider A/B Quality Validation

## Why the source was reduced

The full 575-character `Golden_Set:1` unit produced three prior timeout requests and no translation. Stage 12.2.3 therefore froze a shorter contiguous excerpt from the same source unit without rewriting, summarizing, reordering or resampling it.

The excerpt is deterministically reconstructed from offsets `[0, 153)` of the original Stage 10.10.1 unit. Its SHA-256 is `518ea1f76d7bca5f4ed1a9f534b14524e680d5593c7e17317fde026a4313e63b`. The selection covers the human-reviewed `인간` lexical risk, long Korean modifier-order and narrative-naturalness risks, and ambiguous relationships that must not be concretized.

## Provider execution

Exactly two new NVIDIA requests were made with frozen model, timeout, retry, max-output, generation parameters, glossary and previous context. Baseline succeeded after 61.949 seconds and its unmodified Provider text was preserved. Candidate executed independently but timed out after 180.097 seconds. Neither request was retried or replaced, and fallback was disabled.

The final status is `ab_pair_partial`. Because Candidate has no translation, review status is `not_reviewable_pair_incomplete`; no human A/B comparison can be completed from this pair and no quality conclusion is permitted.

## Scope limitation

Even a complete minimal-excerpt pair would only provide evidence for this 153-character excerpt. It could not be extrapolated to full-chunk, full-chapter or publication-quality performance.

This execution does not establish that the Stage 12.1 Candidate improves quality. Automated metrics and Codex did not score the translation or choose a winner. All manual review fields remain null.

## Frozen boundaries

Stage 12.1 Candidate, Stage 12.2 package, Stage 12.2.1 timeout record and Stage 12.2.2 independent-pair record remain unchanged and integrity-anchored. Prompt, Runtime, Provider, model, timeout, retry and translation strategy were not modified. Stage 12.3 was not started.

Final boundary: `network_requests=2`, `real_provider_executed=true`, `baseline_success=true`, `candidate_success=false`, `new_translation_generated=true`, `comparison_executed=false`, `manual_review_completed=false`, `quality_improvement_verified=false`, and `quality_candidate_accepted=false`.
