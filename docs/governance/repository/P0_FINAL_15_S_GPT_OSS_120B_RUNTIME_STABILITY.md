# P0-FINAL-15-S: Gate B — Runtime Stability

## Baseline
- **HEAD**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **origin/main**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **divergence**: 0/0
- **branch**: main
- **Python**: 3.14.6
- **Timestamp**: 2026-08-29T10:11:04.170621Z

## Candidate
- **Model**: openai/gpt-oss-120b
- **Hosting**: NVIDIA
- **Endpoint**: https://integrate.api.nvidia.com/v1/chat/completions
- **Credential**: NVIDIA_API_KEY

## Test Sequence
Per spec: 3 baseline, 2 narrative, 2 dialogue, 2 continuity, 2 high-context = 11 total observations

## Observations

| Seq | Type | HTTP | Success | Latency (ms) | ReqID | NVCF ReqID | Error |
|-----|------|------|---------|--------------|-------|------------|-------|
| 1 | baseline | 200 | True | 1255 | chatcmpl-8c666d8d9fa9b056 | 7d5b7219-8461-4304-b808-57406a65d49f | None |
| 2 | baseline | 200 | True | 897 | chatcmpl-b59d0c33ae75ed82 | 1be07092-5fad-482d-8933-4dbf179d44f8 | None |
| 3 | baseline | 200 | True | 1257 | chatcmpl-91e7155e201484d4 | 4076f7d9-eda3-4e01-bc0e-12699cb77230 | None |
| 4 | narrative | 200 | True | 10067 | N/A | 489b4888-ec97-4523-b707-c095ed893b54 | None |
| 5 | narrative | 200 | True | 14129 | chatcmpl-b184570078f60a0c | 1f3df8c4-8d88-4623-851f-e3ba2bba0598 | None |
| 6 | dialogue | 200 | True | 5537 | chatcmpl-abba3a0a1c51c5c0 | 159005a4-1214-496d-806c-c3ff4b0d243c | None |
| 7 | dialogue | 200 | True | 4868 | chatcmpl-bd340fa63f438438 | e392d138-9eb3-4f70-81d1-a571b28be1b8 | None |
| 8 | continuity | 200 | True | 4675 | chatcmpl-af3e4a3499912e6e | 86f648be-becd-4633-b879-55facc1fa202 | None |
| 9 | continuity | 200 | True | 4269 | chatcmpl-8d94ec5b34d0801a | 321bf14e-f44f-4457-aa4c-c6418455baac | None |
| 10 | high_context | 200 | True | 32232 | chatcmpl-91cfdfbc3af5c12d | e3335426-a7ed-4b6e-af4a-a49f62975232 | None |
| 11 | high_context | 200 | True | 22401 | chatcmpl-a2ce59b9999a1111 | 32fb4739-b5f6-4195-b3f9-85e3eba099e8 | None |

## Summary

| Metric | Value |
|--------|-------|
| Total Observations | 11 |
| Success Count | 11 |
| Success Rate | 100% |
| Median Latency | 4868ms |
| P95 Latency | 32232ms |
| HTTP 200 | 11 |
| HTTP 429 | 0 |
| HTTP 408 | 0 |
| HTTP 5xx | 0 |

## By Test Type

| Type | Total | Success | Rate | Median Latency |
|------|-------|---------|------|----------------|
| baseline | 3 | 3 | 100% | 1255ms |
| narrative | 2 | 2 | 100% | 14129ms |
| dialogue | 2 | 2 | 100% | 5537ms |
| continuity | 2 | 2 | 100% | 4675ms |
| high_context | 2 | 2 | 100% | 32232ms |

## Gate Result

**PASS**

**Rationale**: Success rate 100% >= 95%

## Limitations
- Single NVIDIA account only
- Observations not statistically independent (sequential)
- No cross-region test
- Single test prompt per category
- No concurrent load test

## Compliance
- ✅ No credential leakage
- ✅ No production modification
- ✅ Read-only provider invocation
- ✅ Root Hygiene compliant
- ✅ Protected Worktree preserved

## Next Gate
Proceed to **Gate C: Context Compatibility** if PASS, otherwise STOP.
