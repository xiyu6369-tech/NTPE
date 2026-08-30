# P0-FINAL-15-S: Gates D/E/F — Translation Quality, Glossary, Continuity

## Baseline
- **HEAD**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **origin/main**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **divergence**: 0/0
- **branch**: main
- **Python**: 3.14.6
- **Timestamp**: 2026-08-29T10:40:41.025426Z

## Candidate
- **Model**: openai/gpt-oss-120b
- **Hosting**: NVIDIA
- **Endpoint**: https://integrate.api.nvidia.com/v1/chat/completions
- **Credential**: NVIDIA_API_KEY

## Gate D — Translation Quality

**Result**: **FAIL**
**Rationale**: Automated quality: avg=67.2, pass=False

| Fixture | Mode | Quality | Status |
|---------|------|---------|--------|
| narrative | base | 68.0 | PASS |
| narrative | glossary | 74.3 | PASS |
| dialogue | base | 53.0 | FAIL |
| dialogue | glossary | 73.2 | PASS |
| continuity | base | 60.6 | FAIL |
| continuity | glossary | 74.2 | PASS |

## Gate E — Glossary Effectiveness

**Result**: **PASS**
**Rationale**: Glossary improvement: +13.4, pass=True

| Fixture | Base Score | Glossary Score | Improvement | Term Base | Term Glossary |
|---------|------------|----------------|-------------|-----------|---------------|
| narrative | 68.0 | 74.3 | +6.4 | 14.5 | 20.0 |
| dialogue | 53.0 | 73.2 | +20.3 | 0.0 | 20.0 |
| continuity | 60.6 | 74.2 | +13.6 | 15.0 | 20.0 |

## Gate F — Continuity

**Result**: **PASS**
**Rationale**: Continuity pass=True

| Fixture | Base Continuity | Glossary Continuity | Base Char | Glossary Char |
|---------|----------------|---------------------|-----------|---------------|
| narrative | 10.0 | 10.0 | 0.0 | 0.0 |
| dialogue | 10.0 | 10.0 | 0.0 | 0.0 |
| continuity | 5.0 | 10.0 | 0.0 | 0.0 |

## Summary

| Metric | Value |
|--------|-------|
| Avg Quality Score | 67.2 |
| Quality Pass | False |
| Avg Glossary Improvement | +13.4 |
| Glossary Pass | True |
| Continuity Pass | True |

## Gate Results

| Gate | Result |
|------|--------|
| D — Translation Quality | FAIL |
| E — Glossary | PASS |
| F — Continuity | PASS |

## Limitations
- Single-run per test condition
- Automated quality scoring only; human review required
- Glossary and character memory are test versions
- Single chunk only; no multi-chunk continuity
- Automated metrics are approximations

## Compliance
- ✅ No credential leakage
- ✅ No production modification
- ✅ Read-only provider invocation
- ✅ Root Hygiene compliant
- ✅ Protected Worktree preserved

## Next Gate
Proceed to **Gate G: Reliability** if all PASS, otherwise STOP.
