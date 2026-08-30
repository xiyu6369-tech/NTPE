# P0-FINAL-15-R — NVIDIA-Hosted Candidate Evaluation

## Phase R-B: NVIDIA-Hosted Models with Current Account Entitlement

### Baseline
- **HEAD**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **origin/main**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **divergence**: 0/0
- **branch**: main
- **Python**: 3.14.6
- **Endpoint**: https://integrate.api.nvidia.com/v1/chat/completions
- **Credential**: NVIDIA_API_KEY
- **Timestamp**: 2026-08-29T09:09:22.165384Z

### Evaluation Pipeline

1. **Smoke Test** (3 observations) - Basic API connectivity
2. **Translation** (3 fixtures × 2 modes) - Narrative, Dialogue, Continuity with Base/Glossary
3. **Quality Scoring** (7 dimensions, threshold ≥65)
4. **Glossary Effectiveness** - Base vs Glossary comparison
5. **Context Compatibility** - Small/Medium/Large fixtures
6. **Reliability** (5 observations) - Success rate, latency

## Results Summary

| Model | Smoke | Translation | Quality | Glossary Δ | Context | Reliability | Classification |
|-------|-------|-------------|---------|------------|---------|-------------|----------------|
| minimaxai/minimax-m3 | 0% | 0% | 0.0 | +0.0 | False | 0% | PROVIDER_UNAVAILABLE |
| deepseek-ai/deepseek-v4-pro-0813 | 100% | 0% | 0.0 | +0.0 | False | 100% | TRANSLATION_UNSUITABLE |
| deepseek-ai/deepseek-v4-flash-0731 | 0% | 0% | 0.0 | +0.0 | False | 0% | PROVIDER_UNAVAILABLE |
| nvidia/nemotron-3-ultra-550b-a55b | 100% | 50% | 73.3 | +0.0 | True | 100% | TRANSLATION_UNSUITABLE |
| nvidia/nemotron-3-super-120b-a12b | 100% | 0% | 0.0 | +0.0 | True | 100% | TRANSLATION_UNSUITABLE |
| nvidia/nemotron-3-nano-30b-a3b | 100% | 50% | 44.5 | +0.0 | True | 100% | TRANSLATION_UNSUITABLE |
| nvidia/nemotron-3.5-lightning-30b-a3b | 100% | 0% | 0.0 | +0.0 | False | 50% | TRANSLATION_UNSUITABLE |
| google/gemma-4-31b-it | 100% | 0% | 0.0 | +0.0 | True | 50% | TRANSLATION_UNSUITABLE |
| openai/gpt-oss-120b | 100% | 100% | 70.8 | +4.4 | True | 100% | REPLACEMENT_CANDIDATE |

## Detailed Results


### minimaxai/minimax-m3

**Classification**: PROVIDER_UNAVAILABLE
**Rationale**: Smoke test failed

**Smoke**: 0% success, median 0ms, P95 0ms, 429s: 2, 408s: 0

**Translation**: 0% success

**Quality Scores**: avg=0.0, pass=False

**Glossary Improvement**: +0.0
**Context Compatible**: False
**Reliability**: 0% success, median 0ms, 429s: 0

### deepseek-ai/deepseek-v4-pro-0813

**Classification**: TRANSLATION_UNSUITABLE
**Rationale**: Translation success rate 0%

**Smoke**: 100% success, median 9749ms, P95 9749ms, 429s: 0, 408s: 0

**Translation**: 0% success
- narrative (base): ✗ HTTP 408 (60111ms)
- narrative (glossary): ✗ HTTP 408 (60098ms)

**Quality Scores**: avg=0.0, pass=False

**Glossary Improvement**: +0.0
**Context Compatible**: False
**Reliability**: 100% success, median 44416ms, 429s: 0

### deepseek-ai/deepseek-v4-flash-0731

**Classification**: PROVIDER_UNAVAILABLE
**Rationale**: Smoke test failed

**Smoke**: 0% success, median 0ms, P95 0ms, 429s: 0, 408s: 2

**Translation**: 0% success

**Quality Scores**: avg=0.0, pass=False

**Glossary Improvement**: +0.0
**Context Compatible**: False
**Reliability**: 0% success, median 0ms, 429s: 0

### nvidia/nemotron-3-ultra-550b-a55b

**Classification**: TRANSLATION_UNSUITABLE
**Rationale**: Translation success rate 50%

**Smoke**: 100% success, median 1139ms, P95 1139ms, 429s: 0, 408s: 0

**Translation**: 50% success
- narrative (base): ✓ HTTP 200 (28658ms)
- narrative (glossary): ✗ HTTP 408 (60081ms)

**Quality Scores**: avg=73.3, pass=True
- narrative_base: 73.3 (Sem=11.3, Flu=17.0, Style=10.0, Term=20.0, Char=0.0, Cont=10.0, Fmt=5.0) [PASS]

**Glossary Improvement**: +0.0
**Context Compatible**: True
**Reliability**: 100% success, median 9056ms, 429s: 0

### nvidia/nemotron-3-super-120b-a12b

**Classification**: TRANSLATION_UNSUITABLE
**Rationale**: Translation success rate 0%

**Smoke**: 100% success, median 1004ms, P95 1004ms, 429s: 0, 408s: 0

**Translation**: 0% success
- narrative (base): ✗ HTTP 408 (60084ms)
- narrative (glossary): ✗ HTTP 408 (60096ms)

**Quality Scores**: avg=0.0, pass=False

**Glossary Improvement**: +0.0
**Context Compatible**: True
**Reliability**: 100% success, median 21650ms, 429s: 0

### nvidia/nemotron-3-nano-30b-a3b

**Classification**: TRANSLATION_UNSUITABLE
**Rationale**: Translation success rate 50%

**Smoke**: 100% success, median 860ms, P95 860ms, 429s: 0, 408s: 0

**Translation**: 50% success
- narrative (base): ✗ HTTP 408 (60083ms)
- narrative (glossary): ✓ HTTP 200 (46887ms)

**Quality Scores**: avg=44.5, pass=False
- narrative_glossary: 44.5 (Sem=0.0, Flu=4.5, Style=10.0, Term=20.0, Char=0.0, Cont=10.0, Fmt=0.0) [FAIL]

**Glossary Improvement**: +0.0
**Context Compatible**: True
**Reliability**: 100% success, median 25091ms, 429s: 0

### nvidia/nemotron-3.5-lightning-30b-a3b

**Classification**: TRANSLATION_UNSUITABLE
**Rationale**: Translation success rate 0%

**Smoke**: 100% success, median 2228ms, P95 2228ms, 429s: 0, 408s: 0

**Translation**: 0% success
- narrative (base): ✗ HTTP 408 (60082ms)
- narrative (glossary): ✗ HTTP 408 (60110ms)

**Quality Scores**: avg=0.0, pass=False

**Glossary Improvement**: +0.0
**Context Compatible**: False
**Reliability**: 50% success, median 41908ms, 429s: 0

### google/gemma-4-31b-it

**Classification**: TRANSLATION_UNSUITABLE
**Rationale**: Translation success rate 0%

**Smoke**: 100% success, median 2752ms, P95 2752ms, 429s: 0, 408s: 0

**Translation**: 0% success
- narrative (base): ✗ HTTP 408 (60119ms)
- narrative (glossary): ✗ HTTP 408 (60099ms)

**Quality Scores**: avg=0.0, pass=False

**Glossary Improvement**: +0.0
**Context Compatible**: True
**Reliability**: 50% success, median 55737ms, 429s: 0

### openai/gpt-oss-120b

**Classification**: REPLACEMENT_CANDIDATE
**Rationale**: All gates passed

**Smoke**: 100% success, median 1172ms, P95 1172ms, 429s: 0, 408s: 0

**Translation**: 100% success
- narrative (base): ✓ HTTP 200 (12992ms)
- narrative (glossary): ✓ HTTP 200 (40845ms)

**Quality Scores**: avg=70.8, pass=True
- narrative_base: 68.7 (Sem=12.5, Flu=15.8, Style=10.0, Term=16.4, Char=0.0, Cont=10.0, Fmt=4.0) [PASS]
- narrative_glossary: 73.0 (Sem=11.7, Flu=17.3, Style=10.0, Term=20.0, Char=0.0, Cont=10.0, Fmt=4.0) [PASS]

**Glossary Improvement**: +4.4
**Context Compatible**: True
**Reliability**: 100% success, median 10010ms, 429s: 0

## Limitations
- Single NVIDIA account only
- Single-run per test condition
- Automated quality scoring only
- No human literary review
- Glossary/char_memory are test versions
- Context tests use estimated tokens

## Compliance
- ✅ No credential leakage
- ✅ No production modification
- ✅ Root Hygiene compliant
- ✅ Protected Worktree preserved
