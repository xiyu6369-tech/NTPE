# TE v7.0 Stage 10.5 — Authorized Single-Invocation Provider Harness

## Status

Stage 10.5 adds an isolated harness that can create exactly one controlled Provider session after explicit authorization. It is disabled by default, is not connected to production translation, and does not automatically execute a Provider.

No real Provider was executed while implementing or validating this stage. Every integration invocation used the fake transport.

## Admission contract

A Provider session is created only when all three independent gates are present:

1. `boundary_enabled=True`
2. `real_provider_enabled=True`
3. a non-empty `authorization_id`

The same admission gates are required for the fake verification path. Fake mode proves the authorized session lifecycle without treating a test as real Provider execution.

The harness also requires a session identifier, exact execution provenance, chunk index 1, the single-chunk flag, and the single-controlled-session flag. One harness instance claims at most one session. A failed or Provider-limited invocation still consumes that claim and cannot be replayed through the same instance.

## Provider boundary

- Endpoint and model are imported from and validated against the Stage 10.4 allowlists.
- The only credential source is `NVIDIA_API_KEY` from the environment.
- Fake mode never reads or receives that credential.
- Fake and callable-real transports implement the same Stage 10.4 invocation contract.
- The callable-real transport is dependency-injected. Stage 10.5 does not include an automatic runner, scheduler, launcher hook, or built-in network request.
- Execution remains single-chunk only and one controlled session only.

“Single invocation” means one controlled harness session. The caller-owned attempt plan may contain bounded retry/fallback attempts inside that session so timeout, HTTP 503, retry, fallback, and independent per-attempt timing evidence remain intact.

## Artifact safety

The optional harness report is metadata-only and integrity-protected. It does not retain the request, prompt, response body, credential, or authorization identifier. Provider results pass through the Stage 10.4 sanitizer before evidence collection.

The report explicitly records that no Baseline artifact, Candidate artifact, Comparison, or Readiness result was created. The harness itself never writes an artifact unless its report writer is explicitly called.

## Frozen boundaries

- No TE v6 Frozen Runtime file is modified.
- `launcher_translate.py` is unchanged.
- No production translation path is connected.
- Stage 10.4, 10.3, 10.2, 10.1, 09, and 08.4.1 contracts remain regression targets.
- No Baseline/Candidate artifacts are created.
- No Comparison or Readiness evaluation is created.
- No Provider is automatically executed.

## Validation

- Stage 10.5 focused integration suite: 25 fake-transport tests.
- Stage 10.5 Root test: focused suite plus manifest integrity.
- Required regression chain: Stage 10.4, 10.3, 10.2, 10.1, 09, 08.4.1, and TE v6 Final Release Freeze.
- Repository validation: `ntpe_validate.py` and `git diff --check`.
