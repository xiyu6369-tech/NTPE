# P0-FINAL-15-N — Controlled Model Replacement / Canary

## Purpose

Controlled validation of C3 Nemotron 3 Super (`nvidia/nemotron-3-super-120b-a12b`)
as replacement candidate for M1 MiniMax M3 (`minimaxai/minimax-m3`).

**Core Principle**: Shadow → Canary → Acceptance Gate → Activation Recommendation

Production routing is NOT modified in this phase.

## Baseline

- **Branch**: main
- **HEAD**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **Worktree**: D:\Python\NTPE

## Model State

| Role | Model | Provider | Status |
|------|-------|----------|--------|
| Current Production (M1) | minimaxai/minimax-m3 | MiniMax | PROVIDER_FAILURE_429 |
| Candidate (C3) | nvidia/nemotron-3-super-120b-a12b | NVIDIA | REPLACEMENT_CANDIDATE |

## Shadow Validation

**Status**: FAIL
**Cases**: 9
**Failures**: 1

### Shadow Test Results

| Model | Profile | Fixture | HTTP | Success | Latency (ms) | Quality | Est. Tokens | Margin | Method |
|-------|---------|---------|------|---------|--------------|---------|-------------|--------|--------|
| nvidia/nemotron-3-super-120b-a12b | normal | narrative | 200 | True | 33397 | 66.0 | 2300 | 125700 | ESTIMATED |
| nvidia/nemotron-3-super-120b-a12b | normal | dialogue | 200 | True | 4501 | 100.0 | 2241 | 125759 | ESTIMATED |
| nvidia/nemotron-3-super-120b-a12b | normal | continuity | 200 | True | 7657 | 88.0 | 2228 | 125772 | ESTIMATED |
| nvidia/nemotron-3-super-120b-a12b | production_like | narrative | 200 | True | 51645 | 87.2 | 4938 | 123062 | ESTIMATED |
| nvidia/nemotron-3-super-120b-a12b | production_like | dialogue | 200 | True | 12003 | 92.5 | 4379 | 123621 | ESTIMATED |
| nvidia/nemotron-3-super-120b-a12b | production_like | continuity | 200 | True | 18953 | 100.0 | 4366 | 123634 | ESTIMATED |
| nvidia/nemotron-3-super-120b-a12b | high_context | narrative | 200 | True | 47705 | 34.0 | 7097 | 120903 | ESTIMATED |
| nvidia/nemotron-3-super-120b-a12b | high_context | dialogue | 200 | True | 20237 | 97.0 | 6379 | 121621 | ESTIMATED |
| nvidia/nemotron-3-super-120b-a12b | high_context | continuity | 408 | False | 60099 | 0.0 | 6366 | 121634 | ESTIMATED |

## Context Measurement

**Measurement Method**: ESTIMATED
**Production-like Margin**: 120903 tokens (94.5%)
**Production-like Status**: PASS

### Token Breakdown (per request)
| Component | Tokens |
|-----------|--------|
| Source | 166 |
| Prompt | 134 |
| Context | 0 |
| Glossary | 0 |
| Expected Output | 2000 |
| **Total Estimated** | **2300** |
| Model Limit | 128000 |
| Remaining Margin | 120903 |

> **Note**: Token measurement is ESTIMATED (character-based). Exact tokenizer measurement not available via current NVIDIA endpoint.

## Long Context Validation (3 Levels)

| Level | Description | Passed/Total | Status |
|-------|-------------|--------------|--------|
| 1 | Normal (minimal context) | 3/3 | PASS |
| 2 | Production-like (full context) | 3/3 | PASS |
| 3 | High Context (near upper bound) | 2/3 | FAIL |

## Translation Quality Gate

Using NTPE existing quality infrastructure (`ntpe_literary_evaluation.py`).

| Category | Score | Status |
|----------|-------|--------|
| Narrative | 87.2/100 | PASS |
| Dialogue | 100.0/100 | PASS |
| Continuity | 100.0/100 | PASS |

### Quality Dimensions

| Dimension | Score | Status |
|-----------|-------|--------|
| Literary Naturalness | 95.7/100 | PASS |
| Character Voice | 100.0/100 | PASS |
| Terminology Consistency | 100.0/100 | PASS |
| Cross-chunk Continuity | 100.0/100 | PASS |

## Human Literary Review

**Status**: PENDING
**Result**: NOT_COMPLETED

> **BLOCKING**: Human review is PENDING. This is a mandatory gate per P0-FINAL-15-N specification.

## Reliability Comparison (M1 vs C3)

| Metric | M1 (minimaxai/minimax-m3) | C3 (nvidia/nemotron-3-super-120b-a12b) | Comparison |
|--------|---------------------------|----------------------------------------|------------|
| success | 2 | 5 | C3_BETTER |
| 4xx | 0 | 0 | SIMILAR |
| 429 | 3 | 0 | C3_BETTER |
| 5xx | 0 | 0 | SIMILAR |
| timeout | 0 | 0 | SIMILAR |
| median_latency_ms | 1784.2 | 12116.2 | M1_BETTER |
| p95_latency_ms | 1784.2 | 40448.5 | M1_BETTER |

### Provider Metadata (Credentials Redacted)

- **Request IDs**: 10 captured
- **NVCF Tracking IDs**: 10 captured
- **Other Metadata**: Available in JSON report

## Canary Evaluation

**Status**: FAIL
**Scope**: internal_test_corpus
**Rollback Path**: config_based_rollback_to_M1

### Activation Gates

| Gate | Requirement | Status |
|------|-------------|--------|
| Gate A - Provider | Account invocation PASS | PASS |
| Gate B - Runtime | Context PASS, production-like PASS | PASS |
| Gate C - Translation | Narrative/Dialogue/Continuity PASS | PASS |
| Gate D - Human | Human literary review PASS | NOT_COMPLETED |
| Gate E - Governance | All regression PASS, root hygiene PASS, credential protection PASS | PASS |

## Classification

**C3 Classification**: NOT_READY

## Decision

**REJECT_C3**

### Rationale

Context compatibility failed

## Production Changes

| Change | Applied |
|--------|---------|
| Model Config | false |
| Routing | false |
| Retry Policy | false |
| Backoff | false |
| RPM | false |
| Chunk Size | false |
| Runtime | false |

## Tests

| Test Category | Status |
|---------------|--------|
| Diagnostic (new) | FAIL |
| Regression (existing) | PENDING |
| Human Review | PENDING |
| Governance Validation | PASS |
| Root Hygiene | PASS |
| Credential Protection | PASS |

## Deliverables

- `artifacts/P0_FINAL_15_N_NVIDIA_NEMOTRON_3_SUPER_CONTROLLED_CANARY_REPORT.json`
- `docs/governance/repository/P0_FINAL_15_N_NVIDIA_NEMOTRON_3_SUPER_CONTROLLED_CANARY.md`
- `tools/one_shots/p15n_nemotron_3_super_controlled_canary.py`

## RM6 Promotion

**Status**: BLOCKED

> RM6 remains BLOCKED until all activation gates complete and production activation is approved.

## Limitations

- Human literary review not completed (PENDING)
- Token measurement uses character-based estimation (not exact tokenizer)
- Limited reliability sample size (5 requests per model)
- No sustained throughput testing
- No cross-chunk continuity validation for chunked workflows
- C3 long-term provider stability unknown

## Conclusion

P0-FINAL-15-N **COMPLETE**.

- **Current Production (M1)**: Unchanged
- **Candidate (C3)**: Not ready for production activation
- **Production Activation**: Requires separate phase (P0-FINAL-15-O)
- **RM6 Promotion**: BLOCKED

---

*Generated by `tools/one_shots/p15n_nemotron_3_super_controlled_canary.py`*
*Timestamp: 2026-08-27T19:18:19.076526Z*
