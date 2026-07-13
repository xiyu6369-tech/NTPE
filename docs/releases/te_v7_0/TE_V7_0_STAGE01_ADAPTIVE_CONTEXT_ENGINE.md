# TE v7.0 Stage 01 Adaptive Context Engine

Adaptive Context Engine (ACE) introduces an independent, deterministic context-selection layer. It ranks context records, calculates a safe dynamic token budget, prioritizes active characters, preserves dialogue lines, compresses narrative context, and produces stable fingerprints, diffs, and metadata-only observability.

## Boundary

Stage 01 does not connect ACE to generation. It does not modify TE v6 Frozen Runtime, Provider routing, Prompt Builder, LTS, or the TE v6 Release Contract. It creates no Provider client and sends no HTTP request. Consumers must explicitly call `build_adaptive_context()` and decide how to use its result in a later approved stage.

## Public API

- `ContextItem`, `RankedContext`, `SelectedContext`, `AdaptiveContextResult`
- `rank_context()` and `calculate_dynamic_budget()`
- `preserve_dialogue()` and `compress_narrative()`
- `context_fingerprint()` and `diff_context()`
- `build_context_observability()` and `build_adaptive_context()`

## Behavior

Ranking combines context kind, relevance, recency, continuity, required status, and active-character overlap. Required records sort ahead of optional records. Dialogue reduction only retains complete dialogue lines. Narrative reduction retains complete leading sentences when possible. Other oversized optional records fail closed and are omitted.

Observability contains IDs, counts, kind totals, budget usage, and preservation/compression counts. It deliberately does not retain raw context text.

The context fingerprint covers only each selected item's ID, kind, and selected-content SHA-256. It does not cover characters, ranking scores, source metadata, budget, or observability.

## Known limitations

- Token estimation is deterministic and conservative, but is not a Provider tokenizer.
- Dialogue recognition uses punctuation and line-shape heuristics; speaker attribution is outside Stage 01.
- Narrative compression is extractive, not semantic summarization.
- ACE is not wired into Prompt generation or runtime execution in Stage 01.

## Rollback

Rollback is removal of the explicit ACE API call by a future consumer. Since Stage 01 has no runtime auto-hook, existing TE v6 behavior is unchanged.
