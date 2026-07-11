# TE v6.0 Stage 05 — Adaptive Retry Decision Engine

## Purpose

Centralize post-quality runtime routing into one Translation Discipline decision engine.

## Actions

- `accept`
- `accept_with_warnings`
- `local_repair`
- `provider_retry`
- `reject`

## Routing policy

- Deterministic orthography, formatting, and soft naturalness issues use local repair or warning acceptance.
- Completeness, residue, terminology, repetition, hallucination, and added-detail issues require provider retry.
- Critical issues without an approved route are rejected.

## Compatibility

The stage preserves existing quality score and severity calculation. Existing `smart_local_repair` metadata remains available for v5 consumers. Provider, timeout, 40 RPM, retry delays, resume, best-attempt selection, and segment recovery are unchanged.
