# TE v6.0 Stage 03 — Discipline Quality Enforcement

Stage 03 makes the Translation Discipline Engine the canonical routing source
for Unified Quality issues while preserving all existing v5 score and decision
semantics.

## Behavior

- Every merged quality issue receives a discipline rule mapping when available.
- Every issue receives a non-destructive route: `local_repair`,
  `provider_retry`, or `warning`.
- Smart Local Repair consumes the discipline route when present and falls back
  to the legacy v5 code tables for older reports.
- Unified score, decision, accepted state, and retry threshold are unchanged.
- No Provider client is created and no external request is added.

## Compatibility

Provider timeout, 40 RPM throttling, retry, backpressure, resume, best-attempt,
segment recovery, Prompt Compiler, Prompt Discipline, and Adaptive Feedback are
unchanged.
