# TE v7.0 Stage 06 — ACE Canary Production Validation

Stage 06 adds an explicit production-validation harness for the single-chunk ACE canary introduced in Stage 05.

## Safety boundary

- Canary remains disabled by default.
- Exactly one configured chunk may activate.
- Any unsafe candidate falls back to the original prompt package.
- Provider timeouts are reported as external limitations, not ACE safety failures.
- Reports and audits are content-redacted.
- No Provider client, HTTP request, retry policy, Prompt policy, LTS, or TE v6 frozen contract is changed.

## CLI

`--ace-canary-validate` enables an isolated canary validation session. Use `--ace-canary-chunk`, `--ace-canary-context-tokens`, and optionally `--ace-canary-report`.

The validation report is ready only when the canary safely activates and the requested regression completes successfully. A Provider failure yields `pass_with_external_provider_limitation` when ACE safety invariants remain intact.
