# TE v7.0 Stage 03 — ACE Runtime Shadow Activation

## Status

Candidate, validated on the TXT production path without Provider calls.

## Purpose

Stage 03 activates the Stage 02 ACE integration in the actual TXT prompt-package construction path while preserving the returned package byte-for-byte at the Python data-contract level. It is a shadow-only runtime hook: ACE analysis runs only when `NTPE_TE_V7_ACE_MODE=shadow`; the original package remains the sole package used downstream.

## Runtime hook

`ntpe_production_translate.py` installs an idempotent wrapper around `lts.txt_translation_runtime.build_prompt_package`. The LTS file itself is not modified. The wrapper calls the original builder, performs redacted shadow analysis, records metrics, and returns the original package object unchanged.

## Modes

- `disabled` (default): wrapper is installed but performs no ACE work and emits no record.
- `shadow`: runs ACE analysis, records redacted metrics, and returns the original package unchanged.
- `active`: Stage 03 does not activate active replacement in the production TXT path. Active integration remains explicit-call-only through Stage 02 APIs.

## Audit

In-memory records are available through `shadow_records()`. Optional JSONL audit output is enabled by setting `NTPE_TE_V7_ACE_SHADOW_AUDIT` to a path. Records include hashes, counts, token estimates, admission/fallback state, and latency only. Source/context text is not retained.

## Safety invariants

- No Provider client is created.
- No HTTP request is sent.
- Provider calls added: 0.
- Returned prompt package remains equal to the baseline package.
- Shadow failures cannot replace or partially merge context.
- TE v6 Runtime, Provider, Prompt Builder, LTS source, and Release Contract remain unchanged.

## Assembly-only benchmark

Golden Set, five chunks:

- Runtime shadow records: 5
- Payload-equivalent chunks: 5/5
- Provider calls: 0
- Baseline estimated context tokens: 2514
- ACE estimated context tokens: 2514
- Estimated reduction: 0
- Admission: 0/5
- Fallback/no-reduction: 5/5

The zero reduction is expected under the current production context window and default budget: ACE correctly refuses replacement when it cannot demonstrate a token reduction. This benchmark validates runtime shadow wiring and payload equivalence only. It does not establish improved translation quality, Provider latency, timeout rate, or API cost.

## Rollback

Remove the Stage 03 import/install call from `ntpe_production_translate.py`, or leave `NTPE_TE_V7_ACE_MODE` unset/disabled. The LTS runtime requires no rollback.
