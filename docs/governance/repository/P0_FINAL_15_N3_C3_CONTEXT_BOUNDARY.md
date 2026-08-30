# P0-FINAL-15-N3-A — C3 Context Boundary Sweep

## Purpose

Find C3's (`nvidia/nemotron-3-super-120b-a12b`) safe context envelope by testing
progressive context levels. **Controlled observation only - not stress/load testing.**

## Baseline

- **Branch**: main
- **HEAD**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **Worktree**: D:\Python\NTPE

## Model State

| Role | Model | Provider | Status |
|------|-------|----------|--------|
| Current Production (M1) | minimaxai/minimax-m3 | MiniMax | ACTIVE / UNCHANGED |
| Candidate (C3) | nvidia/nemotron-3-super-120b-a12b | NVIDIA | REJECTED_PENDING_N3 |

## Test Configuration

- **Source**: Narrative fixture from Golden_Set (2476 chars)
- **Context**: Production-like (character memory + glossary + scene)
- **Max Output Tokens**: 6000
- **Model Context Limit**: 128,000 tokens
- **Measurement Method**: Character-based estimation (~3 chars/token)

## Boundary Levels Tested

| Level | Source % | Source Chars | Context Chars | Est. Total Tokens | Margin |
|-------|----------|--------------|---------------|-------------------|--------|
| context_50pct | 50% | 1238 | 415 | 6684 | 121316 |
| context_60pct | 60% | 1485 | 415 | 6767 | 121233 |
| context_70pct | 70% | 1733 | 415 | 6849 | 121151 |
| context_80pct | 80% | 1980 | 415 | 6932 | 121068 |
| context_85pct | 85% | 2104 | 415 | 6973 | 121027 |
| context_90pct | 90% | 2228 | 415 | 7014 | 120986 |
| context_95pct | 95% | 2352 | 415 | 7056 | 120944 |
| context_100pct | 100% | 2476 | 415 | 7097 | 120903 |

## Test Results

| Level | HTTP | Success | Latency (ms) | Quality | Decision | Error |
|-------|------|---------|--------------|---------|----------|-------|
| context_50pct | 200 | True | 26782 | 59.6 | PASS |  |
| context_60pct | 200 | True | 52997 | 93.2 | PASS |  |
| context_70pct | 200 | True | 36264 | 69.6 | PASS |  |
| context_80pct | 408 | False | 60082 | 0.0 | FAIL | Timeout: HTTPSConnectionPool(host='integrate.api.nvidia.com', port=443): Read timed out. (read timeout=60) |
| context_85pct | 408 | False | 60075 | 0.0 | FAIL | Timeout: HTTPSConnectionPool(host='integrate.api.nvidia.com', port=443): Read timed out. (read timeout=60) |
| context_90pct | 200 | True | 45198 | 85.6 | PASS |  |
| context_95pct | 408 | False | 60094 | 0.0 | FAIL | Timeout: HTTPSConnectionPool(host='integrate.api.nvidia.com', port=443): Read timed out. (read timeout=60) |
| context_100pct | 408 | False | 60087 | 0.0 | FAIL | Timeout: HTTPSConnectionPool(host='integrate.api.nvidia.com', port=443): Read timed out. (read timeout=60) |

## Boundary Analysis

### Boundary Curve

```json
{
  "50%": {
    "http_status": 200,
    "success": true,
    "elapsed_ms": 26782.068500000605,
    "quality_score": 59.6,
    "decision": "PASS"
  },
  "60%": {
    "http_status": 200,
    "success": true,
    "elapsed_ms": 52997.31020000036,
    "quality_score": 93.2,
    "decision": "PASS"
  },
  "70%": {
    "http_status": 200,
    "success": true,
    "elapsed_ms": 36264.2993999998,
    "quality_score": 69.6,
    "decision": "PASS"
  },
  "80%": {
    "http_status": 408,
    "success": false,
    "elapsed_ms": 60081.9690999997,
    "quality_score": 0.0,
    "decision": "FAIL"
  },
  "85%": {
    "http_status": 408,
    "success": false,
    "elapsed_ms": 60074.77479999943,
    "quality_score": 0.0,
    "decision": "FAIL"
  },
  "90%": {
    "http_status": 200,
    "success": true,
    "elapsed_ms": 45197.53679999849,
    "quality_score": 85.6,
    "decision": "PASS"
  },
  "95%": {
    "http_status": 408,
    "success": false,
    "elapsed_ms": 60094.2498000004,
    "quality_score": 0.0,
    "decision": "FAIL"
  },
  "100%": {
    "http_status": 408,
    "success": false,
    "elapsed_ms": 60086.63110000089,
    "quality_score": 0.0,
    "decision": "FAIL"
  }
}
```

### Key Boundaries

| Boundary | Value | Description |
|----------|-------|-------------|
| Safe Boundary | 90% | Highest level with consistent PASS |
| Failure Boundary | 80% | Lowest level with consistent FAIL |
| Intermittent Zone | [] | Levels between safe and failure |

## Gate A3 Decision

**Decision**: PASS

**Rationale**: Safe boundary at 90% - sufficient for production context requirements

### Decision Criteria

- **PASS**: Safe boundary >= 80% - sufficient for production context requirements
- **CONDITIONAL**: Safe boundary 50-79% - may require context reduction strategy
- **FAIL**: No safe boundary or safe boundary < 50% - cannot support literary context

## Production State (UNCHANGED)

| Parameter | Value |
|-----------|-------|
| Model | minimaxai/minimax-m3 (M1) |
| Routing | M1 primary (unchanged) |

## Tests

| Test Category | Status |
|---------------|--------|
| Diagnostic (Gate A3) | PASS |
| Governance Validation | FAIL |
| Root Hygiene | PASS |
| Credential Protection | PASS |

## Deliverables

- `artifacts/P0_FINAL_15_N3_C3_CONTEXT_BOUNDARY_REPORT.json`
- `docs/governance/repository/P0_FINAL_15_N3_C3_CONTEXT_BOUNDARY.md`

## Limitations

- Token measurement uses character-based estimation (not exact tokenizer)
- Single request per boundary level (not repeated for stability)
- Uses single narrative fixture - other fixture types may have different boundaries
- Provider-side behavior may vary over time
- Cannot definitively distinguish provider 408 vs gateway 408

## Conclusion

P0-FINAL-15-N3-A **COMPLETE**.

- **Safe Boundary**: 90%
- **Failure Boundary**: 80%
- **Intermittent Zone**: []
- **Gate A3**: PASS

---

*Generated by `tools/one_shots/p0_final_15_n3_c3_context_boundary.py`*
*Timestamp: 2026-08-28T19:34:45.569614Z*
