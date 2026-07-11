# TE v6.0 Stage 11.3 — Evidence-to-Retry Integration

Stage 11.3 connects reliable Stage 11.2 source–translation alignment evidence to the Stage 10 Adaptive Retry Policy.

## Scope

- Enriches targetable blocking issues only when one unique, reliable, bounded alignment exists.
- Preserves explicit QA evidence and never replaces it.
- Supports safe paragraph-omission insertion evidence and aligned localized ranges.
- Keeps ambiguous or unreliable mappings fail-closed, so Stage 10 continues to use full retry.
- Adds no Provider client, HTTP request, prompt change, score change, or decision change.

## Runtime contract

`core.translation_discipline.runtime_integration` invokes the evidence adapter before building the Stage 10 retry plan. Reliable evidence may change only the retry tier from `full_retry` to `targeted_retry`; quality score and Unified decision remain unchanged.
