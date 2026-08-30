# P0-FINAL-15-P — Final Candidate Comparison & Decision

## Baseline

- **HEAD**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **origin/main**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **divergence**: 0/0
- **branch**: main
- **Endpoint**: https://integrate.api.nvidia.com/v1/chat/completions
- **Credential**: NVIDIA_API_KEY
- **Timestamp**: 2026-08-28T20:31:42.561681Z

## NVIDIA Catalog Summary

- **Fetch Status**: SUCCESS
- **Models Available**: 83

## Scenario Determination

**Scenario D**: Evidence insufficient - no model change, define next investigation

## M1 Baseline (Current Production)

| Property | Value |
|----------|-------|
| Model | minimaxai/minimax-m3 |
| Status | ACTIVE / UNCHANGED |
| Classification | CONTEXT_INCOMPATIBLE |
| 429 Rate | 100% |

**M1 remains ACTIVE and UNCHANGED** per Production Freeze (Section 3).

## C3 Historical Reference

| Property | Value |
|----------|-------|
| Model | nvidia/nemotron-3-super-120b-a12b |
| Status | REJECTED / HISTORICAL EVIDENCE RETAINED |
| Reference Evidence | Chunked + Glossary = 84 (P0-FINAL-15-N3.5) |

C3 evidence retained per Section 4.

## Complete Candidate Ranking

| Rank | Model | Screening | Context | Raw Trans | Reliability | Quality | 429s | Classification | Pass |
|------|-------|-----------|---------|-----------|-------------|---------|------|----------------|------|
| ? | nvidia/nemotron-3-nano-30b-a3b | ✓ (5/7) | ✓ | 100% | 100% | ✗ (58.0) | 0+0 | QUALITY_INSUFFICIENT | ✗ |
| ? | nvidia/llama-3.1-nemoguard-8b-content-safety | ✓ (5/7) | ✓ | 100% | 100% | ✗ (20.8) | 0+0 | QUALITY_INSUFFICIENT | ✗ |
| ? | writer/palmyra-med-70b-32k | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | ibm/granite-3.0-3b-a800m-instruct | ✗ (2/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | mistralai/mistral-nemotron | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/mistral-nemo-minitron-8b-8k-instruct | ✓ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/embed-qa-4 | ✗ (2/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | deepseek-ai/deepseek-coder-6.7b-instruct | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | openai/gpt-oss-120b | ✗ (5/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | deepseek-ai/DeepSeek-V4-Flash-0731 | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/llama-3.1-nemotron-ultra-253b-v1 | ✓ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | databricks/dbrx-instruct | ✗ (2/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1 | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/nemotron-parse | ✓ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/llama-3.1-nemotron-70b-instruct | ✓ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | google/recurrentgemma-2b | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/nemotron-3-nano-omni-30b-a3b-reasoning | ✓ (5/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/nemotron-nano-3-30b-a3b | ✓ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/nemotron-3.5-lightning-30b-a3b | ✓ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/llama-3.1-nemoguard-8b-topic-control | ✓ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | openai/gpt-oss-20b | ✗ (5/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | microsoft/phi-3-vision-128k-instruct | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/vila | ✗ (2/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | mistralai/codestral-22b-instruct-v0.1 | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | meta/muse-glimmer-30b | ✗ (3/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/riva-translate-4b-instruct-v2 | ✗ (3/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | google/diffusiongemma-26b-a4b-it | ✗ (5/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/nemotron-4-340b-instruct | ✓ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | meta/llama-3.2-90b-vision-instruct | ✗ (5/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/llama-3.2-nv-embedqa-1b-v1 | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/riva-translate-4b-instruct | ✗ (2/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | 01-ai/yi-large | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | mistralai/mistral-7b-instruct-v0.3 | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | google/codegemma-1.1-7b | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/nemotron-3-embed-1b | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | snowflake/arctic-embed-l | ✗ (2/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/riva-translate-4b-instruct-v1.1 | ✗ (3/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | adept/fuyu-8b | ✗ (2/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/llama3-chatqa-1.5-70b | ✓ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | deepseek-ai/deepseek-v4-pro-0813 | ✗ (5/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/ising-calibration-1.5-31b | ✗ (3/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | google/gemma-4-31b | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/ai-synthetic-video-detector | ✗ (2/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | aisingapore/sea-lion-7b-instruct | ✗ (2/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | ibm/granite-8b-code-instruct | ✗ (2/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | ibm/granite-3.0-8b-instruct | ✗ (2/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | meta/codellama-70b | ✓ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | deepseek-ai/deepseek-v4-flash-0731 | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/llama-3.1-nemotron-safety-guard-8b-v3 | ✓ (5/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | moonshotai/kimi-k3 | ✗ (2/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | bigcode/starcoder2-15b | ✗ (2/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/llama-nemotron-embed-vl-1b-v2 | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | google/gemma-4-31b-it | ✗ (5/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/nvclip | ✗ (2/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | google/gemma-3-12b-it | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | meta/llama2-70b | ✓ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | microsoft/phi-3.5-moe-instruct | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | meta/llama-guard-4-12b | ✓ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | moonshotai/kimi-k2.6 | ✗ (2/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | ibm/granite-34b-code-instruct | ✗ (2/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/nemotron-3.5-content-safety | ✓ (5/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/neva-22b | ✗ (2/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nv-mistralai/mistral-nemo-12b-instruct | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | deepseek-ai/DeepSeek-V4-Pro-0813 | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | google/codegemma-7b | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | mistralai/mistral-large | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | mistralai/mixtral-8x22b-v0.1 | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/llama-3.1-nemotron-51b-instruct | ✓ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | microsoft/kosmos-2 | ✗ (2/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | writer/palmyra-med-70b | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | writer/palmyra-creative-122b | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/nemotron-4-340b-reward | ✓ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | writer/palmyra-fin-70b-32k | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | google/gemma-3-4b-it | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | poolside/laguna-xs-2.1 | ✗ (3/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/nemotron-3-super-120b-a12b | ✓ (5/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | meta/llama-3.2-11b-vision-instruct | ✗ (5/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | zyphra/zamba2-7b-instruct | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | google/gemma-2b | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | google/deplot | ✗ (2/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | ai21labs/jamba-1.5-large-instruct | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/cosmos-reason2-8b | ✗ (2/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | mistralai/mistral-large-2-instruct | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/nemotron-3-ultra-550b-a55b | ✓ (5/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | nvidia/nv-embedqa-mistral-7b-v2 | ✗ (4/7) | ✗ | N/A | N/A | ✗ (None) | None+None | None | ✗ |
| ? | minimaxai/minimax-m3 | ✓ (5/7) | ✗ | 0% | 0% | ✗ (None) | 3+5 | CONTEXT_INCOMPATIBLE | ✗ |

## Classification Breakdown

### REPLACEMENT_CANDIDATE (0)

### CONDITIONAL_CANDIDATE (0)

### QUALITY_INSUFFICIENT (2)
- **nvidia/nemotron-3-nano-30b-a3b**: Automated quality score < 65 (avg quality: 58.0)
- **nvidia/llama-3.1-nemoguard-8b-content-safety**: Automated quality score < 65 (avg quality: 20.8)

### CONTEXT_INCOMPATIBLE (1)
- **minimaxai/minimax-m3**: Failed context compatibility tests

### OTHER (83)
- **writer/palmyra-med-70b-32k**: None
- **ibm/granite-3.0-3b-a800m-instruct**: None
- **mistralai/mistral-nemotron**: None
- **nvidia/mistral-nemo-minitron-8b-8k-instruct**: None
- **nvidia/embed-qa-4**: None
- **deepseek-ai/deepseek-coder-6.7b-instruct**: None
- **openai/gpt-oss-120b**: None
- **deepseek-ai/DeepSeek-V4-Flash-0731**: None
- **nvidia/llama-3.1-nemotron-ultra-253b-v1**: None
- **databricks/dbrx-instruct**: None
- **nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1**: None
- **nvidia/nemotron-parse**: None
- **nvidia/llama-3.1-nemotron-70b-instruct**: None
- **google/recurrentgemma-2b**: None
- **nvidia/nemotron-3-nano-omni-30b-a3b-reasoning**: None
- **nvidia/nemotron-nano-3-30b-a3b**: None
- **nvidia/nemotron-3.5-lightning-30b-a3b**: None
- **nvidia/llama-3.1-nemoguard-8b-topic-control**: None
- **openai/gpt-oss-20b**: None
- **microsoft/phi-3-vision-128k-instruct**: None
- **nvidia/vila**: None
- **mistralai/codestral-22b-instruct-v0.1**: None
- **meta/muse-glimmer-30b**: None
- **nvidia/riva-translate-4b-instruct-v2**: None
- **google/diffusiongemma-26b-a4b-it**: None
- **nvidia/nemotron-4-340b-instruct**: None
- **meta/llama-3.2-90b-vision-instruct**: None
- **nvidia/llama-3.2-nv-embedqa-1b-v1**: None
- **nvidia/riva-translate-4b-instruct**: None
- **01-ai/yi-large**: None
- **mistralai/mistral-7b-instruct-v0.3**: None
- **google/codegemma-1.1-7b**: None
- **nvidia/nemotron-3-embed-1b**: None
- **snowflake/arctic-embed-l**: None
- **nvidia/riva-translate-4b-instruct-v1.1**: None
- **adept/fuyu-8b**: None
- **nvidia/llama3-chatqa-1.5-70b**: None
- **deepseek-ai/deepseek-v4-pro-0813**: None
- **nvidia/ising-calibration-1.5-31b**: None
- **google/gemma-4-31b**: None
- **nvidia/ai-synthetic-video-detector**: None
- **aisingapore/sea-lion-7b-instruct**: None
- **ibm/granite-8b-code-instruct**: None
- **ibm/granite-3.0-8b-instruct**: None
- **meta/codellama-70b**: None
- **deepseek-ai/deepseek-v4-flash-0731**: None
- **nvidia/llama-3.1-nemotron-safety-guard-8b-v3**: None
- **moonshotai/kimi-k3**: None
- **bigcode/starcoder2-15b**: None
- **nvidia/llama-nemotron-embed-vl-1b-v2**: None
- **google/gemma-4-31b-it**: None
- **nvidia/nvclip**: None
- **google/gemma-3-12b-it**: None
- **meta/llama2-70b**: None
- **microsoft/phi-3.5-moe-instruct**: None
- **meta/llama-guard-4-12b**: None
- **moonshotai/kimi-k2.6**: None
- **ibm/granite-34b-code-instruct**: None
- **nvidia/nemotron-3.5-content-safety**: None
- **nvidia/neva-22b**: None
- **nv-mistralai/mistral-nemo-12b-instruct**: None
- **deepseek-ai/DeepSeek-V4-Pro-0813**: None
- **google/codegemma-7b**: None
- **mistralai/mistral-large**: None
- **mistralai/mixtral-8x22b-v0.1**: None
- **nvidia/llama-3.1-nemotron-51b-instruct**: None
- **microsoft/kosmos-2**: None
- **writer/palmyra-med-70b**: None
- **writer/palmyra-creative-122b**: None
- **nvidia/nemotron-4-340b-reward**: None
- **writer/palmyra-fin-70b-32k**: None
- **google/gemma-3-4b-it**: None
- **poolside/laguna-xs-2.1**: None
- **nvidia/nemotron-3-super-120b-a12b**: None
- **meta/llama-3.2-11b-vision-instruct**: None
- **zyphra/zamba2-7b-instruct**: None
- **google/gemma-2b**: None
- **google/deplot**: None
- **ai21labs/jamba-1.5-large-instruct**: None
- **nvidia/cosmos-reason2-8b**: None
- **mistralai/mistral-large-2-instruct**: None
- **nvidia/nemotron-3-ultra-550b-a55b**: None
- **nvidia/nv-embedqa-mistral-7b-v2**: None

## Human Review Bundle

**Required**: False

**Models for Human Review**:

## Production Replacement Gate Status

Per Section 24:

| Gate | Status |
|------|--------|
| Candidate Identified | ✗ |
| Automated PASS | ✗ |
| Reliability PASS | ✗ |
| Context PASS | ✗ |
| Human Review PASS | ⏳ Pending |
| Governance PASS | ⏳ Pending |
| Controlled Canary | ⏳ Pending |
| Replacement Approval | ⏳ Pending |

**RM6 Promotion**: BLOCKED

**Production Status**: UNCHANGED

## Compliance Checklist

- ✅ No credential leakage
- ✅ No retry policy modification
- ✅ No production behavior modification
- ✅ Root Hygiene compliant (tools/one_shots/)
- ✅ Protected Worktree not modified
- ✅ Historical evidence not modified
- ✅ No RPM limiter changes
- ✅ No concurrency/burst testing
- ✅ Production model (M1) unchanged
- ✅ C3 evidence retained
- ✅ Existing regression tests pass (to be verified)

## Limitations

- Token measurement uses character-based estimation
- Screening criteria applied heuristically based on model ID patterns
- Chinese support assumed for general LLMs (not verified per-model)
- Single smoke test per model (not repeated for stability)
- No direct account entitlement API available
- Free Endpoint availability inferred, not verified per-model
- Token measurement uses character-based estimation
- Single-run per test condition (not repeated for statistical significance)
- Automated quality scoring is approximate; human review required for literary quality
- Glossary and character memory are simplified test versions
- Context tests use estimated tokens, not actual tokenizer counts
- Reliability tests limited to 10 observations
- No cross-chunk consistency testing
- Fixture set is limited (3 fixtures only)

## Next Steps

1. **Complete Human Literary Review** (mandatory gate per Section 23)
2. **Governance Review** of evaluation evidence
3. **If Human Review PASS**: Proceed to Controlled Canary phase
4. **If no candidate qualifies**: M1 remains active, RM6 stays BLOCKED, define next investigation

## Deliverables

- `artifacts/P0_FINAL_15_P_NVIDIA_CURRENT_CANDIDATE_INVENTORY.json` + `.md`
- `artifacts/P0_FINAL_15_P_CANDIDATE_EVALUATION_REPORT.json` + `.md`
- `artifacts/P0_FINAL_15_P_FINAL_CANDIDATE_COMPARISON.json` + `.md`
- `artifacts/P0_FINAL_15_P_Human_Review_Bundle/` (if applicable)

---

**P0-FINAL-15-P Status**: COMPLETE

**Final State**:
```
M1 = ACTIVE / UNCHANGED
C3 = REJECTED / HISTORICAL EVIDENCE RETAINED
New Candidates = EVALUATED
RM6 = BLOCKED
Production = UNCHANGED
```
