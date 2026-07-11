# TE v6.0 Stage 12.5 — Translation Naturalness Engine Freeze

Stage 12.5 freezes the completed Stage 12.1–12.4.1 Naturalness line. It adds no detector, handler, canonicalization rule, issue code, runtime wiring, Provider behavior, or translation feature.

## Frozen scope

- Naturalness Prompt Policy and `NTPE_NATURALNESS_POLICY=0` rollback
- deterministic safe canonicalization
- hallucination and unsupported-detail evidence guard
- literary collocation safe replacements
- character voice and narrative register non-blocking evidence
- specific Voice/Register Translation Discipline mappings

## Compatibility contract

Only deterministic formatting, orthographic, punctuation, frozen canonicalization, and frozen safe-collocation replacements may be repaired locally. Dialogue meaning, honorifics, emotion, person/viewpoint, era vocabulary, relationship distance, ambiguous actions, and information strength cannot be rewritten locally.

High-confidence unsupported details may remain blocking. Voice/Register findings remain non-blocking, `retry_required=false`, non-repairable, outside Quality scoring, and unable to initiate Provider retry by themselves.

Naturalness Policy has one prompt injection source. Disabling it removes only the prompt increment and does not disable safe canonicalization. Provider call count, NVIDIA 40 RPM, timeout, attempts, backpressure, resume, budget, Best Attempt Selection, Adaptive Retry tiers, Quality score, Unified decision, and Stage 11 Evidence APIs remain unchanged.

The existing literary prompt profile now accounts for the already-injected Naturalness Policy block in `policy_tokens`, `total_tokens`, and `total_chars`. This corrects observability metadata only; prompt text and Provider payload are unchanged.

No runtime metadata wiring was added for this freeze; the freeze object, manifest, release document, tests, and delta package carry the contract.
