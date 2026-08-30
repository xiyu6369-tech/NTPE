# TE v7.0 Stage 10.4 — Real Provider Invocation Boundary Contract

## Status

Stage 10.4 defines the isolated admission and invocation boundary required before any real Provider benchmark run. It does not execute a real Provider, create a Baseline/Candidate comparison, or evaluate readiness.

## Contract

- The boundary is disabled by default.
- Real mode requires both the boundary enable and an additional real-Provider enable.
- Real mode also requires a separately supplied authorization identifier.
- Credentials are resolved only from the allowlisted `NVIDIA_API_KEY` environment variable after admission. No API key field or CLI plaintext credential is accepted.
- Provider URL is restricted to `https://integrate.api.nvidia.com/v1/chat/completions`.
- Model is restricted to `meta/llama-3.2-90b-vision-instruct`.
- Execution is single-chunk only.
- Each retry is passed through the Stage 10.2 attempt boundary and receives independent timing evidence.
- timeout, HTTP 503, fallback and retry provenance remain visible in evidence.
- `fake` and `real` bridge provenance must exactly match the configured execution mode.
- Provider results are reduced to status, error, model, fallback and token-usage metadata before evidence collection.
- Request payload, prompt, response body and credentials are never written to the boundary artifact.

## Default verification path

All Stage 10.4 automated tests use `FakeProviderInvocationBridge`. It performs no HTTP request and never receives an API key. The callable real bridge is only an injection boundary; this stage does not provide or invoke a network implementation.

The existence of the real bridge boundary is not authorization to execute it. A real invocation requires separate user authorization and environment readiness at execution time.

## Frozen boundaries

- No production launcher or production translation path is connected.
- Stage 10.3 CLI remains mock-only and unchanged.
- TE v6 Frozen Runtime is unchanged.
- Stage 09 artifacts are unchanged.
- No Provider Baseline or Candidate run is performed.
- No comparison, readiness, rollout or rollback decision is produced.

## Validation

- Stage 10.4 focused integration suite: 21 tests.
- Stage 10.4 Root test validates the focused suite and manifest integrity.
- Stage 10.3, Stage 10.2, Stage 10.1, Stage 09 and TE v6 freeze regressions remain required.
