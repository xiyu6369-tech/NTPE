# TE v6.0 Stage 12.1 — Translation Naturalness Policy & Safe Canonicalization

Stage 12.1 adds a concise generation-time naturalness policy and a provider-free,
fail-closed canonicalizer for deterministic Traditional Chinese novel collocations.
It does not perform subjective semantic rewriting. Ambiguous wording is reported but
left unchanged.

## Runtime boundary

- Prompt policy can be disabled with `NTPE_NATURALNESS_POLICY=0`.
- Safe canonicalization runs after provider output formatting and before Quality Gate.
- Metadata is stored under `prompt_runtime.naturalness_canonicalization`.
- Provider, retry, timeout, resume, Quality score, and Unified decision contracts remain unchanged.
