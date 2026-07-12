# TE v7.0 Stage 07.1 — Manifest Chain Decoupling

## Purpose

Prevent historical Stage root tests from failing whenever a later Stage legitimately updates another manifest.

## Contract

- Source code, tests, and release documents remain protected by fixed SHA-256 values.
- Mutable runtime validation artifacts remain protected by structural and safety validation.
- Nested `manifests/*.json` entries remain in inventory and must exist and parse as valid JSON, but their content hash is not treated as immutable across later Stages.
- No runtime, provider, prompt, retry, QA, or frozen TE v6 behavior changes.

## Scope

The Stage 05.1, Stage 06, Stage 06.1, and Stage 07 root tests now apply the same nested-manifest rule.
