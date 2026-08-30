# P0-FINAL-15-S: Gate A — Provider Invocation Canary

## Baseline
- **HEAD**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **origin/main**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **divergence**: 0/0
- **branch**: main
- **Python**: 3.14.6
- **Timestamp**: 2026-08-29T10:01:43.382858Z

## Candidate Identity
- **Model**: openai/gpt-oss-120b
- **Hosting Provider**: NVIDIA
- **Endpoint**: https://integrate.api.nvidia.com/v1/chat/completions
- **Credential**: NVIDIA_API_KEY

## Observations

| Attempt | HTTP Status | Success | Latency (ms) | Provider ReqID | NVCF ReqID | NVCF Status | Error |
|---------|-------------|---------|--------------|----------------|------------|-------------|-------|
| 1 | 200 | True | 1456 | chatcmpl-ba4b9f5e050c326b | 647a16bc-9cb2-4dd8-b0b5-71a044ace757 | fulfilled | None |
| 2 | 200 | True | 1046 | chatcmpl-81526907e2ce8fe5 | bf8c2d13-9b03-478a-bf93-092267603c25 | fulfilled | None |
| 3 | 200 | True | 1162 | chatcmpl-a74697248b6f864d | 511de7cd-3daf-4963-99f9-f6430f63c17f | fulfilled | None |

## Summary

| Metric | Value |
|--------|-------|
| Total Attempts | 3 |
| Success Count | 3 |
| Success Rate | 100% |
| Median Latency | 1162ms |
| P95 Latency | 1456ms |
| HTTP 200 | 3 |
| HTTP 429 | 0 |
| HTTP 408 | 0 |
| HTTP 5xx | 0 |

## Gate Result

**PASS**

**Rationale**: All 3 smoke attempts returned HTTP 200

## Limitations
- Only 3 smoke attempts (minimum per spec)
- Single endpoint test; no cross-region test
- No rate-limit header validation beyond presence check
- Single test prompt; not comprehensive

## Compliance
- ✅ No credential leakage
- ✅ No production modification
- ✅ Read-only provider invocation
- ✅ Root Hygiene compliant
- ✅ Protected Worktree preserved

## Next Gate
Proceed to **Gate B: Runtime Stability** if PASS, otherwise STOP.
