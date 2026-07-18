# LCR Batch 11.1 Governance Baseline Consumption Audit

## Scope

Batch 11.1 adds a read-only, fail-closed consumer for the committed and tagged Batch 11.0 governance baseline. It does not regenerate, normalize, or modify any Batch 11.0 artifact.

The only accepted source is `manifests/lcr_batch110_governance_freeze_manifest.json`, pinned by SHA-256 to `16148eb7543d877a4544f4bae884987d0f4d14e74873736f9fee0f9d9b4da213`. Alternate manifests, fallback manifests, path traversal, symlink components, malformed schemas, duplicate JSON keys, and non-canonical serialization are rejected.

## Verified frozen contracts

- 18 unique, immutable, governance-frozen capabilities.
- A resolved acyclic dependency graph with no self or orphan dependencies.
- The Batch 10.9 taxonomy remains at 19 types with unchanged semantics.
- The Batch 10.7 one-shot execution claim remains consumed and non-replayable.
- The production shadow hook count remains exactly one.
- `active_production_authorized`, `automatic_rollout_authorized`, `production_integration_authorized`, and `formal_output_replacement_authorized` remain `false`.
- Every Batch 11.0 child manifest and frozen evidence SHA-256 remains valid.

## Boundary guarantees

Batch 11.1 adds zero Provider requests and zero network requests. It does not change runtime, Provider, prompt, resume, output, feature flags, retry, fallback, rollout, or formal output replacement behavior. It creates no active integration path and imports no production execution hook.

Audit output contains only stable governance evidence, violation codes, counts, hashes, Boolean boundary states, and a deterministic fingerprint. It contains no API key, provider payload, raw prompt, source text, response body, or nondeterministic timestamp/UUID.

## Status semantics

- `governance_baseline_consumption_verified`: every pinned baseline and boundary check passed.
- `governance_baseline_consumption_rejected`: a well-formed baseline or frozen artifact drifted.
- `governance_baseline_consumption_invalid`: the requested source or input schema is unsafe or malformed.

The Batch 11.1 activation gate is `lcr_governance_baseline_consumption_verified`. This gate authorizes governance consumption only. It does not authorize production activation, integration, automatic rollout, Provider/network execution, or formal output replacement.

## Validation

The root acceptance wrapper is `ntpe_lcr_batch111_governance_baseline_consumption_audit_test.py`. Focused unit and integration coverage includes positive baseline consumption, all requested drift/replay/path failure classes, three-read byte determinism, Batch 11.0 freeze regression, and sensitive-data exclusion.
