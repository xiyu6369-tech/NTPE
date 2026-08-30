# P0-FINAL-15-S: Gates G/H — Reliability & Latency

## Baseline
- **HEAD**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **origin/main**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **divergence**: 0/0
- **branch**: main
- **Python**: 3.14.6
- **Timestamp**: 2026-08-29T10:46:48.939184Z

## Candidate
- **Model**: openai/gpt-oss-120b
- **Hosting**: NVIDIA
- **Endpoint**: https://integrate.api.nvidia.com/v1/chat/completions
- **Credential**: NVIDIA_API_KEY

## Test Sequence (15 observations)

| Seq | Type | HTTP | Success | Latency (ms) |
|-----|------|------|---------|--------------|
| 1 | normal | 200 | True | 872 |
| 2 | normal | 200 | True | 939 |
| 3 | normal | 200 | True | 887 |
| 4 | narrative | 200 | True | 14901 |
| 5 | narrative | 200 | True | 33623 |
| 6 | dialogue | 200 | True | 5219 |
| 7 | dialogue | 200 | True | 5490 |
| 8 | continuity | 200 | True | 4107 |
| 9 | continuity | 200 | True | 5506 |
| 10 | high_context | 200 | True | 58088 |
| 11 | high_context | 200 | True | 26146 |
| 12 | narrative | 200 | True | 11433 |
| 13 | narrative | 200 | True | 14452 |
| 14 | continuity | 200 | True | 4783 |
| 15 | continuity | 200 | True | 7662 |

## Summary

| Metric | Value |
|--------|-------|
| Total Observations | 15 |
| Success Count | 15 |
| Success Rate | 100% |

## Latency Statistics

| Statistic | All Requests | Successful Only |
|-----------|--------------|-----------------|
| Median | 5506ms | 5506ms |
| P95 | 58088ms | 58088ms |
| Min | 872ms | 872ms |
| Max | 58088ms | 58088ms |

## Failure Classification

| Status | Count |
|--------|-------|

## Gate Results

### Gate G — Reliability
**Result**: **PASS**
**Rationale**: Success rate 100% >= 95%, no systematic failures

### Gate H — Latency
**Result**: **PASS**
**Rationale**: Median latency 5506ms, P95 58088ms (successful requests)

## Limitations
- Sequential observations (not concurrent)
- Single NVIDIA account
- No sustained load test
- No network variability test
- Single test prompt per category

## Compliance
- ✅ No credential leakage
- ✅ No production modification
- ✅ Read-only provider invocation
- ✅ Root Hygiene compliant
- ✅ Protected Worktree preserved

## Next Gate
Proceed to **Gate I: Human Literary Review** if Gate G PASS, otherwise STOP.
