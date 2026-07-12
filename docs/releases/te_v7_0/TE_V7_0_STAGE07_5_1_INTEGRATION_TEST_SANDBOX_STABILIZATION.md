# TE v7.0 Stage 07.5.1 — Integration Test Sandbox Stabilization

## Purpose

Harden the Stage 07.5 Canary A/B integration tests for Windows environments where the global pytest temporary directory is inaccessible.

## Change

The Stage 07.5 integration tests no longer request pytest's `tmp_path` fixture. They create an isolated, UUID-named sandbox under the NTPE project root:

```text
.ntpe_test_sandbox/stage075_canary_ab/<uuid>/
```

The sandbox is removed in `finally` cleanup. Test data remains synthetic and no production translation output is modified.

## Boundaries

No changes were made to:

- Canary A/B evaluation logic
- Runtime or prompt construction
- Provider clients or HTTP behavior
- Quality v5 or QA policy
- LTS or TE v6 frozen layers

## Compatibility

The root test, Stage 07.5 API, and existing call signatures remain unchanged.
