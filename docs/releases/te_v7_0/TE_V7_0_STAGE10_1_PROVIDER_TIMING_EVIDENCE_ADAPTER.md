# TE v7.0 Stage 10.1 — Provider Timing Evidence Adapter

## Status

- Version: `7.0.0-stage10.1`
- Scope: isolated, explicit-call Provider evidence adapter
- Real Provider execution: `not_executed_with_provider`
- Baseline/Candidate Provider benchmark: not started
- Stage 09 artifacts: unchanged

Stage 10.1 supplies the evidence boundary required by the Stage 09 benchmark without modifying the TE v6 frozen runtime, Provider client/policy, timeout, retry, RPM, backpressure, Quality v5, Prompt Policy, or production rollout contracts.

## Existing evidence source

The frozen LTS translation path already returns per-attempt `provider_elapsed_seconds`, `attempt`, `provider_model`, status, and sanitized failure metadata. Stage 10.1 adapts those existing result fields instead of changing their producer. If persisted or supplied timing fields are absent, evidence remains incomplete and fails closed.

For a future caller that can wrap an individual request, `begin_attempt()` and `finish_attempt()` provide an explicit boundary measurement. These methods only observe a caller-owned operation; they do not instantiate a Provider, issue HTTP requests, retry, change timeouts, or select models.

## Evidence contract

Each redacted request record contains:

- pair ID and baseline/candidate run kind;
- set name, chunk index, source hash, and chunk hash;
- model and attempt number;
- request start/end UTC timestamps and elapsed milliseconds;
- success, timeout, HTTP status, or sanitized Provider error category;
- estimated and Provider-reported input/output token counts;
- fallback and suspicious-short-output markers;
- explicit real-provider-execution provenance.

Raw source, translation, prompt, previous context, API key, authorization data, Provider response content, response body, and raw chunk payloads are forbidden.

## Fail-closed behavior

- Adapter use requires explicit opt-in, valid pair ID, and baseline/candidate run kind.
- Resume chunks are recorded only as excluded metadata and never become request timing evidence.
- Missing elapsed time or start/end timestamps produces `provider-timing-evidence-incomplete`.
- Timeout and HTTP 503 remain external Provider conditions rather than ACE functional regressions.
- Complete timing for a failed Provider request remains auditable evidence but returns `evidence_complete_provider_limited`, never benchmark readiness.
- Mock-complete evidence returns `evidence_complete_mock_only`, never benchmark readiness.
- Suspiciously short output blocks readiness so missing output cannot look like a token or latency improvement.
- Mutable evidence artifacts include `content_redacted=true` and a canonical SHA-256 integrity envelope.

## Deferred work

Stage 10.1 does not add CLI flags, runtime hooks, Stage 10 Provider artifacts, real Provider calls, Baseline/Candidate execution, or comparison/readiness decisions. Those remain later Stage 10 increments and require explicit authorization. Stage 09 assembly artifacts are preserved byte-for-byte.
