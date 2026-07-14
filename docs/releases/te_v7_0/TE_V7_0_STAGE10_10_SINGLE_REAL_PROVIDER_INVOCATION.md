# TE v7.0 Stage 10.10A — Single Real Provider Invocation Execution Package

## Status

Stage 10.10A prepares an isolated, one-session execution package for a future explicitly authorized single-chunk real Provider invocation. This delivery stops before Stage 10.10B.

All automated validation used fake transport and a fake `NVIDIA_API_KEY`. Network requests, real Provider executions, and generated translations remained zero.

## Controlled chain

The runner validates and reuses the existing staged contracts:

`Stage 10.9 Preflight → Stage 10.6 CLI contract → Stage 10.5 Harness → Stage 10.4 Boundary → Stage 10.2 Controlled Session → Stage 10.1 Timing Evidence → Stage 10.7 Evidence Pipeline`

The entrypoint only parses safe arguments, obtains the one-time execution authorization through a non-echoing prompt, and delegates to the package. It does not contain Provider, prompt, evidence, or output-guard logic.

## Admission boundary

Execution requires all of the following:

- package, boundary, and real-Provider enables;
- a safe authorization identifier;
- current Stage 10.9 eligibility and canonical Stage 10.9 artifact integrity;
- exact one-time Stage 10.10 execution authorization;
- environment-only `NVIDIA_API_KEY` availability;
- Stage 10.4 provider URL and model allowlists;
- the existing bounded attempt plan with positive timeout and allowlisted fallback models;
- Golden Set chunk 1, produced by the existing chunk planner at frozen chunk size 600;
- exactly one chunk and one controlled session, with resume rejected;
- protected artifact and review paths.

The execution authorization has no CLI argument and is absent from artifacts, reports, exceptions, and safe console output. API keys likewise have no CLI surface and are never retained, measured, truncated, or fingerprinted.

## Prompt and Provider reuse

The runner uses the existing `LiteraryPromptBuilder` without changing its policy or profile. The future real transport delegates its single request to the existing `NvidiaClient`, preserving the caller-owned timeout/attempt plan and Stage 10.4 endpoint/model boundary. No production launcher or general production translation path is connected.

The transport is not constructed in fake mode. Stage 10.10A tests explicitly fail if a real client or socket is opened.

## Output and evidence safety

Provider output is retained only in memory long enough to run these guards:

- empty output;
- suspicious short output;
- high Hangul residue;
- obvious truncation;
- invalid response format;
- Provider refusal;
- timeout, HTTP 503, exception, retry, and fallback provenance.

Evidence artifacts retain only identities, fingerprints, safe attempt/timing/token classifications, preservation flags, execution/network counters, output-guard signals, and integrity. They do not contain source text, prompt, payload, response body, translation, credential, authorization identifier, execution authorization, or exception body.

A future successful Stage 10.10B output may be written only to the separate human-review text file. That review file is outside the evidence integrity payload and is never a production or quality artifact.

## Fixed non-claims

- `comparison_executed = false`
- `readiness_evaluated = false`
- `baseline_created = false`
- `candidate_created = false`
- `production_ready = false`
- `human_review_required = true`

Stage 10.10A's mutable artifact records `stage1010a_fake_transport_validated`, `network_requests = 0`, `real_provider_execution = false`, and `translation_output_generated = false`.

## Validation

- Focused integration suite: 48 fake-transport tests.
- Root test: focused suite, manifest integrity, and mutable artifact integrity.
- Required regression chain: Stage 10.9 through 10.1, Stage 09, Stage 08.4.1, TE v6 Final Release Freeze, `ntpe_validate.py`, and `git diff --check`.

No Stage 10.10B request was issued. A separate user message containing the exact execution authorization is still required before any real invocation.
