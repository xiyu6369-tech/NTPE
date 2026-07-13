# TE v7.0 Stage 10.3 — Controlled Provider Session CLI Harness

## Status

- Version: `7.0.0-stage10.3`
- Default: disabled
- Execution: deterministic mock only
- Real Provider execution: forbidden
- Single chunk: required
- Production path: not connected
- Stage 10 readiness: not evaluated

Stage 10.3 adds a standalone CLI entrypoint, `ntpe_provider_benchmark_session.py`, for explicitly invoking the Stage 10.2 controlled session. It does not modify `launcher_translate.py`, `ntpe_production_translate.py`, TE v6/LTS, Provider Runtime, or normal production translation.

## Input boundary

The harness accepts only pair/run metadata, set and chunk identity, SHA-256 source/chunk fingerprints, model/timeout metadata, token estimates, caller-owned attempt plans, deterministic mock outcomes, and a controlled JSON report path.

It has no arguments for input files, source text, prompts, payloads, Provider URLs, API keys, authorization, or real Provider execution. Reports are restricted to `.ntpe_test_sandbox/` or `artifacts/te_v7_stage103/`, preventing Stage 09 artifact overwrite.

## Execution guarantees

- `--enable-controlled-session` is mandatory.
- Exactly one chunk identity enters a run.
- Attempts are supplied by the caller using `MODEL|TIMEOUT|FALLBACK`; the CLI does not add attempts or select fallback.
- The only available bridge is a deterministic in-process mock.
- Resume excludes the chunk without invoking the mock.
- Timeout and HTTP 503 produce `provider_limited` without a quality or readiness decision.
- Suspicious short output remains visible and cannot become ready evidence.
- Output is metadata-only, redacted, and SHA-256 protected.

## Deferred work

Stage 10.3 does not execute a real Provider, create Provider Baseline/Candidate runs, compare runs, evaluate readiness, claim improvements, enter production rollout, or perform rollback. Those require separately authorized later stages.
