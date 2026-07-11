# TE v4.4 Stage-4.4.2 Controlled Execution Admission Gate

Adds a fail-closed gate using the v4.4 contract, v4.0-v4.3 freeze readiness, an explicit feature flag, a v4.3 shadow recommendation, and safe single-chunk metadata.

Admission permits only an injected isolated callback. It does not permit a provider request, fallback, real translation, or result replacement.
