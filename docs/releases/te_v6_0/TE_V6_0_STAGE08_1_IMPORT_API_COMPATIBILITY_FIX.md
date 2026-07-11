# TE v6.0 Stage 08.1 — Import & API Compatibility Fix

## Problem

`core.translation_discipline.__init__` exported the Stage 05 retry-decision API, but
`core/translation_discipline/retry_decision_engine.py` was absent from the project.
This caused Stage 01–08 integration tests to fail during pytest collection with
`ModuleNotFoundError` even though syntax-only validation still passed.

## Fix

- Restore the canonical Stage 05 `retry_decision_engine.py` implementation.
- Add a root smoke test and integration test that verify the physical module,
  package imports, public exports, decision behavior, and metadata contract.

## Compatibility

No Prompt, Provider, timeout, retry cadence, 40 RPM, Quality score, Unified
decision, resume, local repair, orchestrator, audit, or freeze behavior is changed.
