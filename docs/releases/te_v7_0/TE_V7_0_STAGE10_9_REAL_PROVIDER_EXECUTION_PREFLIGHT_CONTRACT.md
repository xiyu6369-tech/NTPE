# TE v7.0 Stage 10.9 — Real Provider Execution Preflight Contract

## Status

Stage 10.9 adds an isolated, fail-closed preflight contract before any separately authorized real Provider invocation. A successful preflight means only:

`eligible_for_explicit_real_provider_authorization`

It does not execute a Provider, issue a network request, translate content, create Baseline/Candidate artifacts, compare results, or evaluate readiness.

## Admission checks

The contract verifies all of the following before eligibility:

- Stage 10.4 endpoint, model, provider, and credential-environment allowlists.
- Explicit boundary enable, explicit real-Provider enable, and a safe-format authorization identifier.
- `NVIDIA_API_KEY` presence via a boolean-only check.
- Single chunk, one controlled session, non-resume source identity, and SHA-256-shaped source fingerprint.
- A non-empty sequential attempt plan, positive timeouts, an explicit retry ceiling, and allowlisted fallback models.
- A `.json` artifact destination restricted to `artifacts/te_v7_stage109/` or the test sandbox, with Stage 09 overwrite paths rejected.
- Integrity and frozen-boundary fields of the canonical Stage 10.8 fake-transport freeze artifact.
- TE v6 final-release manifest identity, frozen stages, Provider invariant, and every file-inventory SHA-256.
- The Stage 10.6 entrypoint remains disconnected from production launchers and translation runtime.

## Credential and content safety

The caller must provide an environment mapping explicitly. Tests supply only a fake `NVIDIA_API_KEY` value. The preflight converts credential presence directly to a boolean and does not retain the key, its length, prefix, suffix, or fingerprint.

Artifacts do not retain the authorization identifier, source identity, source fingerprint, source text, prompt, payload, response, exception body, or Provider secret. Reports are redaction-checked and integrity-protected.

## Fixed non-execution fields

Every artifact records:

- `network_requests = 0`
- `provider_executed = false`
- `translation_output_generated = false`
- `baseline_created = false`
- `candidate_created = false`
- `comparison_executed = false`
- `readiness_evaluated = false`
- `content_redacted = true`

Even an eligible result requires a separate future user authorization and has no callable Provider transport.

## Validation

- Focused integration suite: 48 tests using fake credentials and fake dependencies only.
- Root test: focused suite, manifest integrity, and mutable preflight-artifact integrity.
- Regression chain: Stage 10.8 through 10.1, Stage 09, Stage 08.4.1, TE v6 Final Release Freeze, `ntpe_validate.py`, and `git diff --check`.

No Stage 10.10 or Stage 11 work is included.
