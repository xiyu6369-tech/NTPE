# P0-FINAL-15-R — Final Decision

## Phase R Final Decision

### Baseline
- **HEAD**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **origin/main**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **divergence**: 0/0
- **branch**: main
- **Endpoint**: https://integrate.api.nvidia.com/v1/chat/completions
- **Credential**: NVIDIA_API_KEY
- **Timestamp**: 2026-08-29T09:35:02.789366Z

## Scenario & Decision

**Scenario A**: One REPLACEMENT_CANDIDATE found

**Decision**: **REPLACEMENT_CANDIDATE_READY**

**Rationale**: Scenario A: One REPLACEMENT_CANDIDATE identified ({'model_id': 'openai/gpt-oss-120b', 'provider': 'NVIDIA', 'api_type': 'NVIDIA integration', 'classification': 'REPLACEMENT_CANDIDATE', 'smoke_success_rate': 1.0, 'translation_success_rate': 1.0, 'avg_quality_score': 70.8, 'quality_pass': True, 'glossary_improvement': 4.4, 'context_compatible': True, 'reliability_success_rate': 1.0, 'smoke_429_count': 0, 'reliability_429_count': 0, 'smoke_median_latency_ms': 1172.1858000018983, 'reliability_median_latency_ms': 10010.048600001028, 'rationale': 'All gates passed'}). All automated gates passed. Human literary review required before canary.

## Best Candidate
- **Model**: openai/gpt-oss-120b
- **Provider**: NVIDIA
- **Classification**: REPLACEMENT_CANDIDATE
- **Smoke**: 100%
- **Translation**: 100%
- **Quality**: 70.8 (PASS)
- **Glossary Improvement**: +4.4
- **Context Compatible**: True
- **Reliability**: 100%

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

**Decision**: APPROVE_REPLACEMENT / CONDITIONAL / REJECT

## M1 Status

| Property | Value |
|----------|-------|
| Model | minimaxai/minimax-m3 |
| Production State | **ACTIVE / UNCHANGED** |
| P15-P Classification | PROVIDER_UNAVAILABLE |
| Reconciled Classification | **M1_PROVIDER_FAILURE_429_PERSISTENT** |
| 429 Rate | 100% (persistent across all observations) |
| Root Cause | UNRESOLVED - provider-side failure |

**Recommendation**: Retain M1 as ACTIVE. Do not replace until root cause resolved.

## C3 Status

| Property | Value |
|----------|-------|
| Model | nvidia/nemotron-3-super-120b-a12b |
| Status | REJECTED / HISTORICAL EVIDENCE RETAINED |
| P15-P Classification | TRANSLATION_UNSUITABLE |
| Reconciled Classification | **PROVIDER_RUNTIME_COMPATIBILITY_LIMITATION** |
| Key Evidence | Chunked + Glossary = 84/100; high-context 408 timeouts |

**Recommendation**: Retain REJECTED status. Evidence retained (Chunked+Glossary=84). Not intrinsic limitation.

## P Candidates (Previous Phase)

| Model | Status | Note |
|-------|--------|------|
| nvidia/llama-3.1-nemoguard-8b-content-safety | QUALITY_INSUFFICIENT | Safety/guardrail model |
| nvidia/nemotron-3-nano-30b-a3b | QUALITY_INSUFFICIENT | Quality < 65 |

## New Candidates (NVIDIA Evaluation)

| Metric | Count |
|--------|-------|
| Total Evaluated | 9 |
| REPLACEMENT_CANDIDATE | 1 |
| TRANSLATION_UNSUITABLE | 6 |
| PROVIDER_UNAVAILABLE | 2 |

## Cross-Provider Candidates (Pending)

- **Count**: 15
- **Status**: Not evaluated (no API credentials available)
- **Providers**: OpenAI, Anthropic, Google, Cohere, Mistral AI, DeepSeek, Z.ai

## Classification Corrections (Evidence Reconciliation)

| Model | From | To | Reason |
|-------|------|-----|--------|
| minimaxai/minimax-m3 | CONTEXT_INCOMPATIBLE | M1_PROVIDER_FAILURE_429_PERSISTENT | 429 at all context sizes; no rate-limit headers; no entitlement denial |
| nvidia/nemotron-3-super-120b-a12b | REJECT_C3 / MODEL_INTRINSIC_LIMITATION | PROVIDER_RUNTIME_COMPATIBILITY_LIMITATION | Model CAN translate (84/100 with chunked+glossary); limitation is high-context runtime stability |

## Next Phase

**Next Phase**: P0-FINAL-15-S

**Rationale**: Proceed to controlled canary after human review PASS

## Final State

```
M1 = ACTIVE / UNCHANGED
C3 = REJECTED / RETAINED
P_Candidates = RECONCILED
New_Candidates = EVALUATED (NVIDIA)
Cross_Provider_Candidates = PENDING (no credentials)
RM6 = BLOCKED
Production = UNCHANGED
```

## Compliance Checklist

- ✅ No credential leakage
- ✅ No production behavior modification
- ✅ No retry policy modification
- ✅ No RPM limiter changes
- ✅ No timeout/backoff/chunk size changes
- ✅ Root Hygiene compliant
- ✅ Protected Worktree preserved
- ✅ Historical evidence retained
- ✅ Regression tests pass

## Limitations
- NVIDIA evaluation only (cross-provider candidates not evaluated due to credential constraints)
- Single-run per test condition; no statistical significance
- Automated quality scoring only; human literary review required
- Glossary and character memory are simplified test versions
- Context tests use estimated token counts
- M1 429 root cause unresolved without provider documentation
- Cross-provider candidates not evaluated - requires credential provisioning

## P0-FINAL-15-R Completion Status

**COMPLETE**

All required deliverables produced:
- `artifacts/P0_FINAL_15_R_NVIDIA_ACCESS_BOUNDARY_REPORT.json` + `.md`
- `artifacts/P0_FINAL_15_R_M1_429_RECONCILIATION.json` + `.md`
- `artifacts/P0_FINAL_15_R_CROSS_PROVIDER_CANDIDATE_INVENTORY.json` + `.md`
- `artifacts/P0_FINAL_15_R_NVIDIA_CANDIDATE_EVALUATION.json` + `.md`
- `artifacts/P0_FINAL_15_R_FINAL_CANDIDATE_COMPARISON.json` + `.md`
- `artifacts/P0_FINAL_15_R_FINAL_DECISION.json` + `.md`

---

**P0-FINAL-15-R Status**: COMPLETE

**Final Principle Applied**:
> **Evidence first. Candidate second. Production last.**
> **沒有明確證據支持 replacement，就不替換。**
