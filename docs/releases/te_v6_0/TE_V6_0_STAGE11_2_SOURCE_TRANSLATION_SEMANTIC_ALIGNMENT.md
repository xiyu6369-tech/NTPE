# TE v6.0 Stage 11.2 — Source–Translation Semantic Alignment

Stage 11.2 adds an offline, monotonic source-to-translation alignment layer on top of the Stage 11.1 Translation Evidence foundation.

## Scope

- Paragraph and sentence alignment ranges.
- Conservative 1:1, 2:1, and 1:2 monotonic mappings.
- Confidence and reliability scoring.
- Fail-closed handling for ambiguous or unbounded mappings.
- Alignment-derived evidence for later targeted recovery stages.

## Safety boundary

This stage does not integrate with Provider, Translation Runtime, Quality decisions, Adaptive Retry, or Golden Set execution. It does not guess source or translated offsets. An omission insertion range is marked reliable only when bounded by reliable surrounding alignment anchors.

## Compatibility

Stage 11.1 APIs and schemas remain available. The new alignment APIs are additive and `runtime_integrated` remains `false`.
