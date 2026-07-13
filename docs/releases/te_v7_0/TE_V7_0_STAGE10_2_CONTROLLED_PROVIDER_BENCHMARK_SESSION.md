# TE v7.0 Stage 10.2 — Controlled Provider Benchmark Session Wiring

## Status

- Version: `7.0.0-stage10.2`
- Default: disabled
- Validation mode: mock-only
- Real Provider execution: `not_executed_with_provider`
- CLI/runtime hook: not connected
- Stage 10 readiness: not evaluated

Stage 10.2 connects the Stage 10.1 evidence adapter to an isolated, explicit-call, single-chunk session. It accepts a caller-owned attempt plan and an injected Provider callable. It does not create a Provider client, issue HTTP requests by itself, or enter normal production translation.

## Attempt-plan boundary

The caller supplies an ordered list of attempts with model, timeout, fallback marker, and token estimates. The session validates that attempts are sequential, then executes only that plan. It never increases attempts, changes timeout, selects another model, inserts fallback, sleeps, or implements a parallel retry policy.

Each attempt uses Stage 10.1 `begin_attempt()` and `finish_attempt()`. Failed attempts remain separate records; a later success cannot overwrite their timing. Total latency is the sum of all executed request evidence.

## Provider bridge guarantees

The bridge receives a deep copy of the caller payload. It neither modifies the original payload nor rewrites prompt/model settings. Provider output content is not retained; only status, sanitized error category, timing, model, fallback, and token metadata reach evidence artifacts.

Resume chunks are excluded before invoking the injected Provider callable. Timeout and HTTP 503 produce `provider_limited`, remain external conditions, and do not create an ACE quality verdict.

## Session states

- `completed`: at least one caller-planned attempt succeeded.
- `provider_limited`: all executed attempts failed under external Provider conditions.
- `failed`: attempts failed without an external-condition classification.
- `excluded`: resume chunk; no Provider callable invocation.

Mock evidence remains `evidence_complete_mock_only`. A controlled session always reports `readiness_evaluated=false`; Baseline/Candidate comparison and Stage 10 readiness remain later stages.

## Deferred work

This stage does not add public CLI flags, real Provider execution, production artifacts, Baseline/Candidate runs, comparison, readiness, rollout, rollback, or any TE v6/LTS/Provider Runtime modification. Stage 09 artifacts remain byte-for-byte unchanged.
