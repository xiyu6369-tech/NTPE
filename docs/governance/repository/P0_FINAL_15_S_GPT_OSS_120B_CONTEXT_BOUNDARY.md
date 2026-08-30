# P0-FINAL-15-S: Gate C — Context Compatibility

## Baseline
- **HEAD**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **origin/main**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **divergence**: 0/0
- **branch**: main
- **Python**: 3.14.6
- **Timestamp**: 2026-08-29T10:23:23.081882Z

## Candidate
- **Model**: openai/gpt-oss-120b
- **Hosting**: NVIDIA
- **Endpoint**: https://integrate.api.nvidia.com/v1/chat/completions
- **Credential**: NVIDIA_API_KEY

## Context Levels Tested

| Level | Description | Input Tokens | Output Max |
|-------|-------------|--------------|------------|
| L1_normal | Single narrative | ~850 | 4000 |
| L2_large | 2x narrative | ~1675 | 8000 |
| L3_upper_bound | 4x narrative (production upper-bound) | ~3326 | 16000 |

## Results

| Level | HTTP | Success | Latency | Timeout | Truncation | Corruption |
|-------|------|---------|---------|---------|------------|------------|
| L1_normal | 200 | True | 13052ms | False | False | False |
| L2_large | 200 | True | 59682ms | False | True | False |
| L3_upper_bound | 200 | True | 25404ms | False | False | False |

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | 3 |
| Pass Count | 3 |
| Pass Rate | 100% |

## Gate Result

**FAIL**

**Rationale**: Context compatibility failure: 3/3 levels pass

## Limitations
- Token estimation is character-based approximation
- Single run per context level (no repetition)
- No streaming test
- No token budget test with actual tokenizer
- Production workload may differ from test fixtures

## Compliance
- ✅ No credential leakage
- ✅ No production modification
- ✅ Read-only provider invocation
- ✅ Root Hygiene compliant
- ✅ Protected Worktree preserved

## Next Gate
Proceed to **Gate D: Translation Quality** if PASS, otherwise STOP.
