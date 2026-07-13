# TE v6.0 Stage 10 — Adaptive Retry Policy 2.0

Stage 10 adds a centralized, backward-compatible recovery plan after the Unified Quality Gate. It preserves the Stage 01–09 public APIs and does not change prompt text, scoring, Provider configuration, timeout/backpressure, resume, or NVIDIA's process-wide 40 RPM ceiling.

## Recovery tiers

| Tier | Behavior | Provider use |
|---|---|---|
| `none` | Accept clean or warning-only output | None |
| `local_repair` | Run only registered deterministic handlers, then revalidate | None |
| `targeted_retry` | Regenerate bounded source units supported by reliable QA evidence | One request per unit by default |
| `full_retry` | Regenerate the chunk only when local targeting is unsafe or unsuccessful | Recovery budget permitting |
| `reject` | Fail closed for an unknown critical issue | None |

`NATURALNESS_GUARD` without a deterministic handler remains warning-only. Targeted recovery requires explicit in-bounds source offsets, `reliable=true`, and confidence of at least 0.70. The policy never derives offsets from string similarity and never treats source offsets as translated-text offsets.

## Provider budget

`NTPE_CHUNK_PROVIDER_BUDGET` defaults to two extra recovery requests per chunk. `NTPE_TARGETED_RETRY_MAX_UNITS` defaults to two and `NTPE_TARGETED_RETRY_ATTEMPTS` defaults to one. These recovery limits do not redefine the existing `--provider-attempts` value used for a normal Provider request. All Provider calls remain owned by the LTS runtime and the existing NVIDIA global limiter remains capped at 40 RPM.

## Compatibility and integration

`integrate_translation_discipline_runtime` remains the sole Stage 09 entrypoint. `DisciplineRuntimeResult` adds retry tier, plan, evidence, units, and budget fields while retaining every existing field. The Stage 09 `final_action=provider_retry` vocabulary remains compatible; Stage 10 consumers use `retry_tier` to distinguish targeted from full retry.

The existing `apply_adaptive_local_repairs`, `apply_adaptive_retry_decision`, `orchestrate_runtime_discipline`, segment recovery, Best Attempt, and Adaptive Feedback APIs remain available.

## Safety

Targeted merge is allowed only with an explicit translated range supplied by quality evidence. Missing or conflicting evidence fails closed to full retry. Every repaired candidate must be revalidated, and Best Attempt Selection remains responsible for retaining a better earlier candidate after a failed recovery.
