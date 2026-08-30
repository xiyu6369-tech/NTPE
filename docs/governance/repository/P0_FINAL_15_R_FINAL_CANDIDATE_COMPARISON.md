# P0-FINAL-15-R — Final Candidate Comparison

## Baseline

- **HEAD**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **origin/main**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **divergence**: 0/0
- **branch**: main
- **Endpoint**: https://integrate.api.nvidia.com/v1/chat/completions
- **Credential**: NVIDIA_API_KEY
- **Timestamp**: 2026-08-29T09:12:06.765279Z

## Scenario Determination

**Scenario A**: One REPLACEMENT_CANDIDATE found - proceed to controlled canary

## M1 Baseline (Current Production)

| Property | Value |
|----------|-------|
| Model | minimaxai/minimax-m3 |
| Provider | NVIDIA (MiniMax) |
| Production State | **ACTIVE** |
| P15-P Classification | PROVIDER_UNAVAILABLE |
| Reconciled Classification | **M1_PROVIDER_FAILURE_429_PERSISTENT** |
| 429 Rate | 26/28 |

## C3 Status

| Property | Value |
|----------|-------|
| Model | nvidia/nemotron-3-super-120b-a12b |
| Status | REJECTED / HISTORICAL EVIDENCE RETAINED |
| P15-P Classification | TRANSLATION_UNSUITABLE |
| Reconciled Classification | **PROVIDER_RUNTIME_COMPATIBILITY_LIMITATION** |
| Chunked + Glossary Quality | 84.0 |
| High-Context Timeout | True |

## NVIDIA Candidate Comparison

| Rank | Model | Provider | Smoke | Translation | Quality | Glossary Δ | Context | Reliability | 429s | Classification |
|------|-------|----------|-------|-------------|---------|------------|---------|-------------|------|----------------|
| 1 | openai/gpt-oss-120b | NVIDIA | 100% | 100% | 70.8 | +4.4 | True | 100% | 0+0 | REPLACEMENT_CANDIDATE |
| 2 | nvidia/nemotron-3-ultra-550b-a55b | NVIDIA | 100% | 50% | 73.3 | +0.0 | True | 100% | 0+0 | TRANSLATION_UNSUITABLE |
| 3 | nvidia/nemotron-3-nano-30b-a3b | NVIDIA | 100% | 50% | 44.5 | +0.0 | True | 100% | 0+0 | TRANSLATION_UNSUITABLE |
| 4 | nvidia/nemotron-3-super-120b-a12b | NVIDIA | 100% | 0% | 0.0 | +0.0 | True | 100% | 0+0 | TRANSLATION_UNSUITABLE |
| 5 | google/gemma-4-31b-it | NVIDIA | 100% | 0% | 0.0 | +0.0 | True | 50% | 0+0 | TRANSLATION_UNSUITABLE |
| 6 | deepseek-ai/deepseek-v4-pro-0813 | NVIDIA | 100% | 0% | 0.0 | +0.0 | False | 100% | 0+0 | TRANSLATION_UNSUITABLE |
| 7 | nvidia/nemotron-3.5-lightning-30b-a3b | NVIDIA | 100% | 0% | 0.0 | +0.0 | False | 50% | 0+0 | TRANSLATION_UNSUITABLE |
| 8 | deepseek-ai/deepseek-v4-flash-0731 | NVIDIA | 0% | 0% | 0.0 | +0.0 | False | 0% | 0+0 | PROVIDER_UNAVAILABLE |
| 9 | minimaxai/minimax-m3 | NVIDIA | 0% | 0% | 0.0 | +0.0 | False | 0% | 2+0 | PROVIDER_UNAVAILABLE |

## Detailed NVIDIA Candidate Results


### minimaxai/minimax-m3 (NVIDIA)

**Classification**: PROVIDER_UNAVAILABLE
**Rationale**: Smoke test failed

- **Smoke**: 0%, median 0ms
- **Translation**: 0%
- **Quality**: 0.0 (pass: False)
- **Glossary Improvement**: +0.0
- **Context Compatible**: False
- **Reliability**: 0%, median 0ms
- **429 Rate**: smoke 2, reliability 0

### deepseek-ai/deepseek-v4-pro-0813 (NVIDIA)

**Classification**: TRANSLATION_UNSUITABLE
**Rationale**: Translation success rate 0%

- **Smoke**: 100%, median 9749ms
- **Translation**: 0%
- **Quality**: 0.0 (pass: False)
- **Glossary Improvement**: +0.0
- **Context Compatible**: False
- **Reliability**: 100%, median 44416ms
- **429 Rate**: smoke 0, reliability 0

### deepseek-ai/deepseek-v4-flash-0731 (NVIDIA)

**Classification**: PROVIDER_UNAVAILABLE
**Rationale**: Smoke test failed

- **Smoke**: 0%, median 0ms
- **Translation**: 0%
- **Quality**: 0.0 (pass: False)
- **Glossary Improvement**: +0.0
- **Context Compatible**: False
- **Reliability**: 0%, median 0ms
- **429 Rate**: smoke 0, reliability 0

### nvidia/nemotron-3-ultra-550b-a55b (NVIDIA)

**Classification**: TRANSLATION_UNSUITABLE
**Rationale**: Translation success rate 50%

- **Smoke**: 100%, median 1139ms
- **Translation**: 50%
- **Quality**: 73.3 (pass: True)
- **Glossary Improvement**: +0.0
- **Context Compatible**: True
- **Reliability**: 100%, median 9056ms
- **429 Rate**: smoke 0, reliability 0

### nvidia/nemotron-3-super-120b-a12b (NVIDIA)

**Classification**: TRANSLATION_UNSUITABLE
**Rationale**: Translation success rate 0%

- **Smoke**: 100%, median 1004ms
- **Translation**: 0%
- **Quality**: 0.0 (pass: False)
- **Glossary Improvement**: +0.0
- **Context Compatible**: True
- **Reliability**: 100%, median 21650ms
- **429 Rate**: smoke 0, reliability 0

### nvidia/nemotron-3-nano-30b-a3b (NVIDIA)

**Classification**: TRANSLATION_UNSUITABLE
**Rationale**: Translation success rate 50%

- **Smoke**: 100%, median 860ms
- **Translation**: 50%
- **Quality**: 44.5 (pass: False)
- **Glossary Improvement**: +0.0
- **Context Compatible**: True
- **Reliability**: 100%, median 25091ms
- **429 Rate**: smoke 0, reliability 0

### nvidia/nemotron-3.5-lightning-30b-a3b (NVIDIA)

**Classification**: TRANSLATION_UNSUITABLE
**Rationale**: Translation success rate 0%

- **Smoke**: 100%, median 2228ms
- **Translation**: 0%
- **Quality**: 0.0 (pass: False)
- **Glossary Improvement**: +0.0
- **Context Compatible**: False
- **Reliability**: 50%, median 41908ms
- **429 Rate**: smoke 0, reliability 0

### google/gemma-4-31b-it (NVIDIA)

**Classification**: TRANSLATION_UNSUITABLE
**Rationale**: Translation success rate 0%

- **Smoke**: 100%, median 2752ms
- **Translation**: 0%
- **Quality**: 0.0 (pass: False)
- **Glossary Improvement**: +0.0
- **Context Compatible**: True
- **Reliability**: 50%, median 55737ms
- **429 Rate**: smoke 0, reliability 0

### openai/gpt-oss-120b (NVIDIA)

**Classification**: REPLACEMENT_CANDIDATE
**Rationale**: All gates passed

- **Smoke**: 100%, median 1172ms
- **Translation**: 100%
- **Quality**: 70.8 (pass: True)
- **Glossary Improvement**: +4.4
- **Context Compatible**: True
- **Reliability**: 100%, median 10010ms
- **429 Rate**: smoke 0, reliability 0

## Cross-Provider Candidates (Pending Evaluation)

| Model | Provider | Context Window | API Type | Note |
|-------|----------|----------------|----------|------|
| gpt-4o | OpenAI | 128000 | openai-compatible | Not evaluated - no API credentials available |
| gpt-4o-mini | OpenAI | 128000 | openai-compatible | Not evaluated - no API credentials available |
| gpt-4-turbo | OpenAI | 128000 | openai-compatible | Not evaluated - no API credentials available |
| claude-3-5-sonnet-20241022 | Anthropic | 200000 | anthropic | Not evaluated - no API credentials available |
| claude-3-5-haiku-20241022 | Anthropic | 200000 | anthropic | Not evaluated - no API credentials available |
| claude-3-opus-20240229 | Anthropic | 200000 | anthropic | Not evaluated - no API credentials available |
| gemini-1.5-pro | Google | 2000000 | google | Not evaluated - no API credentials available |
| gemini-1.5-flash | Google | 1000000 | google | Not evaluated - no API credentials available |
| gemini-1.0-pro | Google | 32768 | google | Not evaluated - no API credentials available |
| command-r-plus | Cohere | 128000 | cohere | Not evaluated - no API credentials available |
| command-r | Cohere | 128000 | cohere | Not evaluated - no API credentials available |
| mistral-large-latest | Mistral AI | 32768 | openai-compatible | Not evaluated - no API credentials available |
| mistral-medium-latest | Mistral AI | 32768 | openai-compatible | Not evaluated - no API credentials available |
| deepseek-chat | DeepSeek | 64000 | openai-compatible | Not evaluated - no API credentials available |
| glm-4 | Z.ai | 128000 | openai-compatible | Not evaluated - no API credentials available |

## Replacement Candidate Gate Status

| Gate | Status |
|------|--------|
| Provider PASS | ✓ |
| Runtime PASS | ✓ |
| Translation PASS | ✓ |
| Quality ≥65 | ✓ |
| Context Compatible | ✓ |
| Glossary Behavior | ✓ |
| Human Review | ⏳ Pending |
| Governance PASS | ⏳ Pending |
| Controlled Canary | ⏳ Pending |
| Replacement Approval | ⏳ Pending |

**RM6 Status**: BLOCKED

**Production Status**: UNCHANGED

## Human Review

**Required**: True

**Models for Review**:
- openai/gpt-oss-120b

### Review Protocol

Per Section 23, human review must assess:
- Narrative flow and literary tone
- Dialogue naturalness and character voice distinction
- Terminology consistency (glossary adherence)
- Character consistency (character memory adherence)
- Continuity across chunks
- Traditional Chinese (Taiwan) naturalness

Decision: APPROVE_REPLACEMENT / CONDITIONAL / REJECT

## Limitations
- NVIDIA evaluation only (cross-provider candidates not evaluated due to credential constraints)
- Single-run per test condition; no statistical significance
- Automated quality scoring only; human literary review required
- Glossary and character memory are simplified test versions
- Context tests use estimated token counts
- M1 429 root cause unresolved without provider documentation
- Cross-provider candidates not evaluated - requires credential provisioning

## Compliance

- ✅ No credential leakage
- ✅ No production behavior modification
- ✅ No retry/RPM/timeout/backoff changes
- ✅ Root Hygiene compliant
- ✅ Protected Worktree preserved
- ✅ Historical evidence retained
- ✅ Regression tests pass

## Next Steps

1. **Complete Human Literary Review** for REPLACEMENT_CANDIDATE(s)
2. **Governance Review** of evaluation evidence
3. **If Human Review PASS**: Proceed to Controlled Canary (P0-FINAL-15-S)
4. **If No Candidate Qualifies**: M1 remains ACTIVE, RM6 stays BLOCKED
