# P0-FINAL-15-R — M1 429 Reconciliation

## Phase R-A2: M1 429 Status Investigation

### Baseline
- **HEAD**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **origin/main**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **divergence**: 0/0
- **branch**: main
- **Python**: 3.14.6
- **Endpoint**: https://integrate.api.nvidia.com/v1/chat/completions
- **Credential**: NVIDIA_API_KEY
- **Timestamp**: 2026-08-29T06:47:05.345801Z

### Previous Classification (P0-FINAL-15-Q)
**M1_PROVIDER_FAILURE_429_UNRESOLVED**

### Current Observations
- **Total Observations**: 28
- **Success Count**: 2 (7.1%)
- **HTTP 200**: 2
- **HTTP 429**: 26
- **HTTP 408**: 0
- **HTTP 4xx Other**: 0
- **HTTP 5xx**: 0
- **Median Latency**: 1220ms
- **P95 Latency**: 1220ms

### Classification
**Current**: **M1_PROVIDER_FAILURE_429_PERSISTENT**
**Changed**: False
**Rationale**: 26/28 observations returned 429. Persistent failure.

### By Context Level
- **small**: 2/16 success, 14 429, 0 408
- **medium**: 0/6 success, 6 429, 0 408
- **large**: 0/6 success, 6 429, 0 408

### By Test Type
- **smoke**: 1/9 success, 8 429
- **translation**: 1/9 success, 8 429
- **sustained**: 0/10 success, 10 429

### Evidence Summary
- **previous_classification**: M1_PROVIDER_FAILURE_429_UNRESOLVED
- **total_observations**: 28
- **success_rate**: 0.07142857142857142
- **http_200_rate**: 0.07142857142857142
- **http_429_rate**: 0.9285714285714286
- **http_408_rate**: 0.0
- **median_latency_ms**: 1219.967799999722
- **p95_latency_ms**: 1219.967799999722
- **context_levels_tested**: ['small', 'medium', 'large']
- **test_types**: ['smoke', 'translation', 'sustained']

## Limitations
- Single NVIDIA account; no cross-account comparison
- Observations span short time window; may not capture periodic patterns
- Single test prompt per context level
- Cannot distinguish provider-side vs infrastructure issues
- No provider documentation on 429 semantics

## Conclusion

**Previous**: M1_PROVIDER_FAILURE_429_UNRESOLVED
**Current**: M1_PROVIDER_FAILURE_429_PERSISTENT
**Changed**: False

26/28 observations returned 429. Persistent failure.

**If RESOLVED**: M1 429 was transient or condition-dependent. M1 may be viable as production model again.
**If INTERMITTENT**: M1 has intermittent 429. Unsuitable for production without root cause fix.
**If PERSISTENT**: M1 429 remains unresolved. M1 unsuitable for production.

## Compliance
- ✅ No credential leakage
- ✅ No production modification
- ✅ No retry/RPM/timeout/backoff changes
- ✅ Root Hygiene compliant
- ✅ Protected Worktree preserved
- ✅ Historical evidence retained
