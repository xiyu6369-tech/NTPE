# TE v6.0 Stage 12.3 — Literary Collocation and Direct-Translation Guard

## Scope

Stage 12.3 adds a deterministic literary-collocation boundary after Stage 12.1 canonicalization and before quality evaluation. It repairs only expressions with a stable Traditional Chinese correction and records warnings for ambiguous source-dependent wording.

## Safe repairs

- redundant conditional collocations such as `若要是…`
- clearly awkward interaction collocations such as `和他纏繞在一起`
- redundant aspect particles such as `用著冷漠的眼神`
- fixed weather collocations with a stable Chinese rendering

## Fail-closed warnings

Ambiguous expressions such as `嘔了一口氣` are not rewritten because the source may mean exhaling, gasping, swallowing, or sighing. They remain visible as naturalness warnings.

## Compatibility

This stage does not change Provider configuration, request count, Quality score, Unified decision, retry tier, timeout, resume, or the NVIDIA 40 RPM limit.
