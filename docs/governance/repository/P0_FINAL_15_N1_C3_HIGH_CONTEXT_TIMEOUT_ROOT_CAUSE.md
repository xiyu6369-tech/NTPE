# P0-FINAL-15-N1 — C3 High-Context Timeout Root-Cause Investigation

## Purpose

Investigate the root cause of HTTP 408 timeout on C3 (`nvidia/nemotron-3-super-120b-a12b`)
for Level 3 high_context / continuity workload.

**Core Principle**: Diagnose only. No production behavior modification.

## Scope

### In Scope
- Reproduction of Level 3 408
- Request composition accounting
- Context isolation (removing one component at a time)
- Source size boundary analysis
- Context accumulation boundary
- Temporal/transient behavior test
- Chunking diagnostic
- Provider metadata collection
- Client vs Provider timeout boundary classification
- Human literary review

### Out of Scope
- Production model change
- Production routing change
- Retry/backoff/RPM modification
- Timeout policy modification
- Chunk size modification
- Stress/concurrency testing
- Provider load testing

## Baseline

- **Branch**: main
- **HEAD**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **Worktree**: D:\Python\NTPE
- **Git Status**: Clean

## Reproduction

**Test**: N1-03 (Level 3 Full Context - Continuity)
**HTTP Status**: 200
**Reproducible**: NO
**Latency**: 7158ms
**Error Type**: SUCCESS
**Timeout Classification**: N/A
**Provider Request ID**: N/A
**NVCF ReqID**: 22f21530-a283-4b91-925d-78529bd02e86

## HTTP 408 Source Analysis

**Classification**: N/A

- **Provider-Generated 408**: Response body contains timeout/NVCF indicators
- **Client-Generated 408**: requests.exceptions.Timeout exception
- **Unknown**: Cannot determine from available evidence

**Response Body Preview**:
```
{"id":"chatcmpl-c4f4d24f-148a-4a54-bca5-c8d57a001f91","choices":[{"index":0,"message":{"content":"金哲秀是一名擁有三十年經驗的刑警。他所負責的案件總是複雜多變，但他憑藉自己獨特的直覺，不斷挖掘真相。他的夥伴李英熙則與他完全相反，是一位只靠邏輯與證據來破案的原則主義者。\n\n有一天，兩人被指派處理一起連續失踪案。哲秀試圖從現場的微細痕跡中尋找線索，英熙則分析受害者的共同點。起初兩人對彼此的方法持懷疑態度，但很快意識到他們的做法其實互補。哲秀的直覺引導了英熙的邏輯，而英熙的證據則支撐了哲秀的推測。","role":"assistant","reasoning_content":"We need to translate Korean text to Traditional Chinese (Taiwan). Must preserve character names and honorifics. The text is about detective Kim Cheol-su and pa
```

**NVCF Metadata**:
- NVCF ReqID: 22f21530-a283-4b91-925d-78529bd02e86
- NVCF Status: fulfilled
- Retry-After: N/A
- Rate Limit Headers: None

## Request Composition (Baseline Level 3)

| Component | Chars | Est. Tokens |
|-----------|-------|-------------|
| Source Text | 283 | 94 |
| System Prompt | 404 | 134 |
| Character Memory | 135 | 45 |
| Glossary | 54 | 18 |
| Recent Scene | 226 | 75 |
| **Output Budget** | N/A | 6000 |
| **Total Estimated** | N/A | **6366** |
| **Model Context Limit** | N/A | **128000** |
| **Context Margin** | N/A | **121634** |

**Measurement Method**: ESTIMATED

## Context Isolation Tests

| Test | Components Removed | HTTP Status | Success | Latency | Error Type | Tokens | Margin |
|------|-------------------|-------------|---------|---------|------------|--------|--------|
| N1-04_no_optional_context | opt_ctx=True, memory=False, glossary=False | 200 | True | 37894ms | SUCCESS | 6291 | 121709 |
| N1-05_no_memory | opt_ctx=False, memory=True, glossary=False | 200 | True | 12181ms | SUCCESS | 6321 | 121679 |
| N1-06_no_glossary | opt_ctx=False, memory=False, glossary=True | 200 | True | 11107ms | SUCCESS | 6348 | 121652 |
| N1-07_no_context_no_memory | opt_ctx=True, memory=True, glossary=False | 200 | True | 23103ms | SUCCESS | 6246 | 121754 |
| N1-08_minimal_prompt_only | opt_ctx=True, memory=True, glossary=True | 200 | True | 9303ms | SUCCESS | 6228 | 121772 |

## Source Size Boundary Tests

| Test | Source Chars | HTTP Status | Success | Latency | Error Type | Tokens | Margin |
|------|--------------|-------------|---------|---------|------------|--------|--------|
| N1-07a_full_source | 283 | 200 | True | 10112ms | SUCCESS | 6366 | 121634 |
| N1-07b_half_source | 141 | 200 | True | 7529ms | SUCCESS | 6319 | 121681 |
| N1-07c_quarter_source | 70 | 200 | True | 10093ms | SUCCESS | 6295 | 121705 |
| N1-07d_minimal_source | 25 | 200 | True | 4453ms | SUCCESS | 6280 | 121720 |

## Context Accumulation Tests

| Test | Components Added | HTTP Status | Success | Latency | Error Type | Tokens | Margin |
|------|-----------------|-------------|---------|---------|------------|--------|--------|
| N1-C1_source_only | opt_ctx=False, memory=False, glossary=False | 200 | True | 15665ms | SUCCESS | 6228 | 121772 |
| N1-C2_plus_glossary | opt_ctx=False, memory=False, glossary=True | 200 | True | 5132ms | SUCCESS | 6246 | 121754 |
| N1-C3_plus_memory | opt_ctx=True, memory=True, glossary=True | 200 | True | 59080ms | SUCCESS | 6366 | 121634 |

## Temporal/Transient Test

| Test | HTTP Status | Success | Latency | Error Type |
|------|-------------|---------|---------|------------|
| N1-09_repeat_1 | 200 | True | 12411ms | SUCCESS |
| N1-09_repeat_2 | 200 | True | 16079ms | SUCCESS |

**Classification**: DETERMINISTIC

## Chunking Diagnostic Test

| Test | Source Chars | HTTP Status | Success | Latency | Error Type | Tokens | Margin |
|------|--------------|-------------|---------|---------|------------|--------|--------|
| N1-10_original_size | 283 | 200 | True | 12822ms | SUCCESS | 6366 | 121634 |
| N1-10_chunk_141chars | 141 | 200 | True | 18195ms | SUCCESS | 6319 | 121681 |
| N1-10_original_size | 283 | 200 | True | 7409ms | SUCCESS | 6366 | 121634 |
| N1-10_chunk_250chars | 250 | 200 | True | 7383ms | SUCCESS | 6355 | 121645 |

## Provider Metadata Summary

All request/response metadata captured with credentials redacted.

## Client/Provider Boundary Analysis

**Current Client Timeout Configuration**:
- Connect Timeout: 10s
- Read Timeout: 60s
- NTPE_API_TIMEOUT: None
- NTPE_API_CONNECT_TIMEOUT: None
- NTPE_CURRENT_API_TIMEOUT: None

**Observed Timeout Classification**: N/A

## Root Cause Classification

**Primary**: NON_REPRODUCIBLE
**Secondary**: None
**Confidence**: LOW

### Evidence

- Root cause: NON_REPRODUCIBLE
- Isolation test(s) PASS when removing: ['N1-04_no_optional_context', 'N1-05_no_memory', 'N1-06_no_glossary', 'N1-07_no_context_no_memory', 'N1-08_minimal_prompt_only']
- Smaller source sizes PASS: ['N1-07a_full_source', 'N1-07b_half_source', 'N1-07c_quarter_source', 'N1-07d_minimal_source']
- Smaller chunks PASS: ['N1-10_original_size', 'N1-10_chunk_141chars', 'N1-10_original_size', 'N1-10_chunk_250chars']

## Workaround Classification

**Type**: DIAGNOSTIC_ONLY
**Description**: Removing certain context components allows success: ['N1-04_no_optional_context', 'N1-05_no_memory', 'N1-06_no_glossary', 'N1-07_no_context_no_memory', 'N1-08_minimal_prompt_only']. Not a production change.

## Human Literary Review

| Category | Status |
|----------|--------|
| Narrative | PENDING |
| Dialogue | PENDING |
| Continuity | PENDING |
| Character Voice | PENDING |
| Terminology | PENDING |
| Traditional Chinese Naturalness | PENDING |
| **Overall** | **PENDING** |

**Notes**: Human literary review not completed. Required for activation gate.

## C3 Replacement Status

**Status**: BLOCKED

- `REPLACEMENT_CANDIDATE_RESTORED`: Root cause resolved + human review PASS
- `REPLACEMENT_CANDIDATE_WITH_CONCERNS`: Root cause identified but not fully resolved, or human review PENDING
- `BLOCKED`: Root cause unknown/unresolved, or human review FAIL

## Production Changes

| Change | Applied |
|--------|---------|
| Model Config | false |
| Routing | false |
| Retry Policy | false |
| Backoff | false |
| RPM | false |
| Timeout | false |
| Chunk Size | false |
| Runtime | false |

## Tests

| Test Category | Status |
|---------------|--------|
| Diagnostic (new) | PASS |
| Regression (existing) | PENDING |
| Governance Validation | PASS |
| Root Hygiene | PASS |
| Credential Protection | PASS |

## Deliverables

- `artifacts/P0_FINAL_15_N1_C3_High_Context_Timeout_Root_Cause_Report.json`
- `docs/governance/repository/P0_FINAL_15_N1_C3_HIGH_CONTEXT_TIMEOUT_ROOT_CAUSE.md`
- `tools/one_shots/p15n1_c3_high_context_timeout_diagnostic.py`

## RM6 Promotion

**Status**: BLOCKED

## Limitations

- Human literary review not completed (PENDING)
- Token measurement uses character-based estimation (not exact tokenizer)
- Limited test sample size (single request per configuration)
- No sustained throughput testing
- Provider-side behavior may vary over time
- Cannot definitively distinguish provider 408 vs gateway 408 without provider documentation

## Conclusion

P0-FINAL-15-N1 **COMPLETE**.

**Root Cause**: NON_REPRODUCIBLE (LOW confidence)

**C3 Status**: BLOCKED

**Production Impact**: ZERO - No production behavior modified.

**Human Review**: PENDING (blocking gate for activation)

**RM6**: BLOCKED

---

*Generated by `tools/one_shots/p15n1_c3_high_context_timeout_diagnostic.py`*
*Timestamp: 2026-08-27T19:58:23.181485+00:00*
