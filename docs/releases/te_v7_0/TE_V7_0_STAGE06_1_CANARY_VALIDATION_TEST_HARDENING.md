# TE v7.0 Stage 06.1 — Canary Validation Test Hardening

Stage 06.1 corrects two validation-only assumptions without changing ACE Canary runtime behavior.

## Changes

- Root validation now verifies exact environment restoration instead of assuming the caller's shell was not already configured for `canary` mode.
- Stage 06 production validation JSON is treated as a mutable execution artifact. Its safety schema is validated while source and contract files remain protected by fixed SHA-256 hashes.
- The Stage 06 integration test no longer depends on pytest's global `tmp_path` directory; it uses a project-local temporary directory and cleans it deterministically.

## Boundaries

No TE v6 frozen file, Provider client, Prompt policy, LTS runtime, Canary activation logic, HTTP behavior, or API configuration is changed.
