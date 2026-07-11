# TE v6.0 Stage 12.4 — Character Voice & Narrative Register Guard

Stage 12.4 adds a deterministic, offline evidence guard after safe canonicalization and literary collocation, and before the unsupported-detail and quality gates.

The guard detects conservative signals for speaker voice or honorific drift, narrative viewpoint/register drift, era-inappropriate expressions, and unsupported emotional amplification. It never rewrites dialogue, honorifics, emotion, person, viewpoint, era vocabulary, or relationship language.

All findings are non-blocking warnings in this stage. Reliable findings (`confidence >= 0.85`) are marked `provider_retry_relevant` and mapped to the existing Translation Discipline registry for later feedback use, but `retry_required` remains false. Unified decisions, scores, retry tiers, Provider budgets, timeout, RPM, and resume behavior are unchanged.

Runtime metadata is stored under `prompt_runtime.voice_register_guard`. The implementation is fail-closed, makes no Provider or HTTP calls, and permits no semantic local rewrite. `NTPE_NATURALNESS_POLICY=0` continues to remove the single Naturalness Policy prompt block.

This stage does not enter Stage 12.5.
