# P0-FINAL-15-R — Candidate Evaluation

## Phase R-B: Cross-Provider Candidate Evaluation

### Baseline
- **HEAD**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **origin/main**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **divergence**: 0/0
- **branch**: main
- **Python**: 3.14.6
- **Timestamp**: 2026-08-29T07:00:17.047999Z

### Candidates Evaluated
- gpt-4o (OpenAI) [openai-compatible]
- gpt-4o-mini (OpenAI) [openai-compatible]
- gpt-4-turbo (OpenAI) [openai-compatible]

## Evaluation Pipeline

1. **Smoke Test** (3 observations) - Basic API connectivity
2. **Translation** (3 fixtures × 2 modes) - Narrative, Dialogue, Continuity with Base/Glossary
3. **Quality Scoring** (7 dimensions, threshold ≥65)
4. **Glossary Effectiveness** - Base vs Glossary comparison
5. **Context Compatibility** - Small/Medium/Large fixtures
6. **Reliability** (5 observations) - Success rate, latency

## Results Summary

| Model | Provider | Smoke | Translation | Quality | Glossary Δ | Context | Reliability | Classification |
|-------|----------|-------|-------------|---------|------------|---------|-------------|----------------|
| gpt-4o | OpenAI | 0% | 0% | 0.0 | +0.0 | False | 0% | PROVIDER_UNAVAILABLE |
| gpt-4o-mini | OpenAI | 0% | 0% | 0.0 | +0.0 | False | 0% | PROVIDER_UNAVAILABLE |
| gpt-4-turbo | OpenAI | 0% | 0% | 0.0 | +0.0 | False | 0% | PROVIDER_UNAVAILABLE |

## Detailed Results


### gpt-4o (OpenAI)

**Classification**: PROVIDER_UNAVAILABLE
**Rationale**: Smoke test failed

**Smoke**: 0% success, median 0ms, P95 0ms

**Translation**: 0% success

**Quality Scores**: avg=0.0, pass=False

**Glossary Improvement**: +0.0
**Context Compatible**: False
**Reliability**: 0% success, median 0ms

### gpt-4o-mini (OpenAI)

**Classification**: PROVIDER_UNAVAILABLE
**Rationale**: Smoke test failed

**Smoke**: 0% success, median 0ms, P95 0ms

**Translation**: 0% success

**Quality Scores**: avg=0.0, pass=False

**Glossary Improvement**: +0.0
**Context Compatible**: False
**Reliability**: 0% success, median 0ms

### gpt-4-turbo (OpenAI)

**Classification**: PROVIDER_UNAVAILABLE
**Rationale**: Smoke test failed

**Smoke**: 0% success, median 0ms, P95 0ms

**Translation**: 0% success

**Quality Scores**: avg=0.0, pass=False

**Glossary Improvement**: +0.0
**Context Compatible**: False
**Reliability**: 0% success, median 0ms

## Limitations
- Only candidates with available API keys evaluated
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
