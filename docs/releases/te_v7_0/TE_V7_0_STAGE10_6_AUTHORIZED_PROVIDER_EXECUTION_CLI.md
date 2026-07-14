# TE v7.0 Stage 10.6 — Authorized Provider Execution CLI

## Status

Stage 10.6 adds a standalone, explicit-call-only CLI around the frozen Stage 10.5 Authorized Single-Invocation Provider Harness. The CLI is disabled by default and requires `--enable-boundary`, `--enable-real-provider`, and a non-empty `--authorization-id` before it can construct an invocation request.

All automated validation uses the deterministic fake transport. No real Provider was executed and no network request was issued.

## Safety boundary

- The CLI delegates execution to Stage 10.5 and does not reimplement Provider logic.
- Provider, endpoint, and model admission reuse the Stage 10.4 allowlists.
- The CLI has no API-key, credential, raw source, prompt, request body, response body, production payload, or launcher-hook argument.
- `NVIDIA_API_KEY` remains the only credential contract. Fake mode does not read it.
- Real mode has no built-in transport and fails closed unless a caller explicitly dependency-injects a Stage 10.5-compatible real transport.
- Exactly one chunk and one controlled session are allowed.
- Reports are restricted to Stage 10 artifact locations or `.ntpe_test_sandbox`; Stage 09 overwrite paths are rejected.

## Non-goals

The CLI is not connected to `launcher_translate.py`, `ntpe_production_translate.py`, or any production translation path. It does not automatically run a Provider, create Baseline or Candidate artifacts, compare results, or evaluate readiness.

## Validation

- Focused integration suite: 25 tests.
- Root test: focused suite plus manifest integrity.
- Required regression chain: Stage 10.5 through 10.1, Stage 09, Stage 08.4.1, and TE v6 Final Release Freeze.
