# TE v7.0 Stage 02 — ACE Opt-in Runtime Integration & Shadow Benchmark

Version: `7.0.0-stage02`

Stage 02 adds an explicit, non-invasive integration boundary around the validated Stage 01.1 Adaptive Context Engine. No TE v6 frozen file is modified.

## Modes

- `disabled` (default): ACE is not executed and the prompt payload remains unchanged.
- `shadow`: ACE is evaluated and redacted metrics are emitted, while the original prompt payload remains byte-semantically equivalent under canonical hashing.
- `active`: ACE context is used only when admission succeeds; otherwise the complete original context is restored.

Environment switch: `NTPE_TE_V7_ACE_MODE=disabled|shadow|active`. Invalid values fail closed to `disabled`.

## Safety

Active admission requires required and locked retention, active-character retention when applicable, non-empty safe selection, budget compliance, and actual estimated token reduction. Fallback never merges partial ACE context with original context.

## Scope

This stage does not auto-hook the legacy runtime, alter provider requests, create a provider client, call HTTP, or claim actual translation-quality/provider-latency improvement. The integration API is explicit-call-only pending a later validated runtime activation stage.

## Benchmark meaning

The artifact is assembly-only. It reports deterministic estimated context-token changes and payload equivalence in shadow mode. It is not Provider tokenizer output and is not an API cost or latency measurement.
