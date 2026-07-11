# TE v6.0 Stage 12.2 — Hallucination and Unsupported Detail Guard

Stage 12.2 adds a conservative, offline guard for high-confidence unsupported specificity in novel translation output.

## Scope

The guard currently detects:

- a controlled set of concrete transport terms absent from the Korean source;
- proper-name-like island names when the source only contains a generic island reference;
- explicit day/hour counts absent from the source.

Only high-confidence, directly corroborated cases produce blocking `ADDED_DETAIL` or `HALLUCINATION` issues. Ambiguous cases remain warnings. The guard never rewrites semantics and never calls a provider.

## Runtime placement

Provider output → safe naturalness canonicalization → unsupported-detail guard → Quality v5 / Unified Quality Gate.

## Compatibility

No change to provider implementation, 40 RPM limit, timeout propagation, resume, best-attempt selection, prompt token profile, or existing quality score algorithm. The guard contributes normal quality issues through the existing Unified Quality Gate.
