# TE v7.0 Stage 10.10.1 — Provider Timeout Evidence and Controlled Retry Contract

## Status

Stage 10.10.1 preserves the committed Stage 10.10B timeout artifact as immutable historical evidence and prepares a separate, fail-closed controlled retry contract. This delivery performs fake-only validation and does not execute a real Provider retry.

The prepared state is limited to `controlled_retry_contract_prepared`. It is not a retry success, translation-quality decision, benchmark result, or production-readiness claim.

## Historical evidence boundary

The canonical Stage 10.10B artifact must remain byte-identical and must verify as:

- `stage = TE-v7.0-Stage10.10B`;
- `status = single_real_invocation_failed`;
- exactly one real network request;
- timeout confirmed;
- no generated translation.

The Stage 10.10.1 artifact records only the prior file SHA-256, safe status, timeout confirmation, and network count. It does not copy the prior artifact body or any sensitive content.

## Frozen retry shape

Any future explicitly authorized retry is fixed to:

- Golden Set chunk 1 at chunk size 600;
- one new invocation identity and one controlled session;
- one attempt only;
- 180-second timeout;
- `meta/llama-3.2-90b-vision-instruct`;
- no fallback;
- the existing Stage 10.4 NVIDIA endpoint allowlist;
- environment-only `NVIDIA_API_KEY`.

The CLI does not expose timeout, attempt count, model, fallback, endpoint, API key, source, prompt, or payload controls. The previous Stage 10.10 authorization is rejected; a distinct Stage 10.10.1 authorization is required for any future real execution.

## Token evidence semantics

The artifact separates:

- `estimated_input_tokens`;
- `estimated_output_token_budget`;
- `actual_input_tokens`;
- `actual_output_tokens`;
- `token_usage_source`;
- `token_usage_complete`.

The 800-token output value is an execution budget, not actual usage. If the Provider supplies no usage response, actual token fields remain null and completeness remains false. Estimated values cannot be used for cost or improvement claims.

## Safety and non-claims

The artifact and console-safe model retain no source text, prompt, request payload, response body, translation, credential, authorization identifier, execution authorization, or exception body.

The prepared artifact fixes:

- `network_requests = 0`;
- `real_provider_execution = false`;
- `retry_executed = false`;
- `translation_output_generated = false`;
- `comparison_executed = false`;
- `readiness_evaluated = false`;
- `baseline_created = false`;
- `candidate_created = false`;
- `production_ready = false`;
- `human_review_required = true`.

No production launcher, TE v6 Frozen Runtime, prompt policy, translation policy, Provider retry policy, or Stage 10.10B artifact is modified.

## Validation

- 47 focused fake-transport tests cover admission, prior-evidence integrity, immutable history, frozen retry parameters, path safety, provenance, timeout/503/exception classification, token semantics, redaction, and integrity tampering.
- The root test validates the focused suite, manifest hashes, canonical prepared artifact, and byte-identical Stage 10.10B evidence.
- The Stage 10.10 through Stage 09 provider-boundary chain, Stage 08.4.1, TE v6 Final Release Freeze, `ntpe_validate.py`, and `git diff --check` remain required regressions.

No real Provider retry is authorized or executed by this release.
