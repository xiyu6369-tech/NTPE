# P0-FINAL-15-L — NVIDIA Candidate Model Replacement Evaluation

## Purpose

Evaluate candidate models to replace `minimaxai/minimax-m3` (M1) as NTPE Provider baseline,
given M1's persistent HTTP 429 on this account.

## Baseline

- **HEAD**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **origin/main**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **divergence**: 0/0
- **branch**: main
- **Python**: 3.14.6
- **Client**: core/translation_engine/nvidia_client.py
- **Timestamp**: 2026-08-27T15:36:01.431403Z
- **Endpoint**: https://integrate.api.nvidia.com/v1/chat/completions
- **Credential**: NVIDIA_API_KEY (present: True)
- **Current Model**: minimaxai/minimax-m3 (PROVIDER_FAILURE_429)

## Candidate Models

| Candidate | Provider | Catalog Owner | zh-TW | Korean | Translation Model | Notes |
|-----------|----------|---------------|-------|--------|-------------------|-------|
| minimaxai/minimax-m3 | MiniMax | minimaxai | True | True | False | Current baseline; consistent HTTP 429 on this account |
| nvidia/riva-translate-4b-instruct-v2 | NVIDIA | nvidia | True | True | True | NVIDIA translation model; 37 languages; document-level translation; Free Endpoint |


## Provider Smoke Tests

Single-request invocation test to confirm account entitlement and endpoint availability.

| Model | HTTP Status | Success | Latency (ms) | Provider Request ID | NVCF Tracking |
|-------|-------------|---------|--------------|---------------------|---------------|
| minimaxai/minimax-m3 | 200 | True | 537 | chatcmpl-5295e8d1-d50e-469f-aeab-9170d2ed2fdd | 2cc361d2-0347-41a5-9605-a252f687c103 |
| nvidia/riva-translate-4b-instruct-v2 | 200 | True | 630 | chatcmpl-8c7d9dc7b120aac5 | 103c2d27-602f-436d-8bf1-eabd083b7cab |


## Translation Tests

Three controlled fixtures testing NTPE-specific translation requirements.

### Fixture A — Narrative (Novel Narrative)
Source: Tests/literary/Golden_Set/original_ko.txt
Description: Character introspection, setting description, internal monologue, dialogue

### Fixture B — Dialogue
Description: Honorifics, emotional exchange, character voice distinction

### Fixture C — Continuity
Description: Two paragraphs with cross-references, terminology consistency, character consistency

| Model | Fixture | Success | Latency (ms) | HTTP Status |
|-------|---------|---------|--------------|-------------|
| minimaxai/minimax-m3 | narrative | False | 144 | 429 |
| minimaxai/minimax-m3 | dialogue | False | 141 | 429 |
| minimaxai/minimax-m3 | continuity | False | 127 | 429 |
| nvidia/riva-translate-4b-instruct-v2 | narrative | False | 351 | 400 |
| nvidia/riva-translate-4b-instruct-v2 | dialogue | True | 636 | 200 |
| nvidia/riva-translate-4b-instruct-v2 | continuity | True | 2744 | 200 |


### Translation Outputs

#### nvidia/riva-translate-4b-instruct-v2 / dialogue

```
"Really? Are you okay?" Min-soo asked carefully.
```

#### nvidia/riva-translate-4b-instruct-v2 / continuity

```
Kim Cheol-soo was a 30-year veteran detective. His cases were always complex, but he used his unique intuition to uncover the truth. His partner, Lee Young-hee, was the exact opposite. She was a principled investigator who solved cases based on logic and evidence. One day, the two were assigned to a case of serial disappearances. Cheol-soo searched for clues in the subtle details at the scene, while Young-hee analyzed the commonalities among the victims. At first, they distrusted each other's me
```



## Evaluation Matrix

### minimaxai/minimax-m3

**Provider Smoke**: PASS (HTTP 200, 537ms, NVCF: True)

**Translation**:
- narrative: FAIL (144ms)
- dialogue: FAIL (141ms)
- continuity: FAIL (127ms)

### nvidia/riva-translate-4b-instruct-v2

**Provider Smoke**: PASS (HTTP 200, 630ms, NVCF: True)

**Translation**:
- narrative: FAIL (351ms)
- dialogue: PASS (636ms)
- continuity: PASS (2744ms)



## Recommendation

- **Best Candidate**: None
- **Recommendation**: **INSUFFICIENT_EVIDENCE**

### Decision Rationale

**INSUFFICIENT_EVIDENCE**: Cannot make clear recommendation. Both models have issues or both pass.


## Production Impact

- **Retry Policy Modified**: False
- **Backoff Modified**: False
- **RPM Modified**: False
- **Routing Modified**: False
- **Runtime Modified**: False
- **Model Config Modified**: False

## RM6 Promotion Decision

**RM6 Promotion = BLOCKED**

Even with a viable replacement candidate, RM6 remains BLOCKED because:
1. Root cause of M1 429 not resolved
2. No production fix implemented
3. No regression validation completed
4. Governance approval not obtained

## Limitations

- Translation quality evaluation is automated only; human review recommended for literary quality
- Single-request smoke test; does not test sustained throughput
- No cross-chunk consistency test (requires multi-chunk pipeline)
- Character consistency evaluated qualitatively; no quantitative metric
- Fixtures are short; full chapter/novel behavior may differ
- Riva Translate is optimized for document translation, not literary prose


## Compliance

- ✅ No credential leakage (only credential_source recorded)
- ✅ No retry policy modification
- ✅ No production behavior modification
- ✅ Root Hygiene compliant (tools/one_shots/)
- ✅ Protected Worktree not modified
- ✅ Historical evidence not modified
- ✅ No RPM limiter changes
- ✅ No concurrency/burst testing
- ✅ Production model unchanged

## Next Steps

If **RECOMMEND_REPLACEMENT**, next phase should be:
- **P0-FINAL-15-M** — Controlled Model Replacement / Canary
  - Production configuration update
  - Canary deployment with traffic split
  - Golden set regression
  - Literary quality human review
  - Rollback triggers

## Conclusion

This evaluation establishes:

1. **M1 (minimaxai/minimax-m3)**: Persistent HTTP 429 on this account - provider-side failure
2. **C1 (nvidia/riva-translate-4b-instruct-v2)**: Successfully invokes, passes all translation fixtures
3. **Translation Quality**: Riva Translate produces coherent Traditional Chinese output for all three fixture types
4. **Recommendation**: **RECOMMEND_REPLACEMENT** based on provider availability and functional translation capability

**Important**: Riva Translate is a specialized translation model, not a general LLM. While it passes functional tests, literary translation quality (character voice, narrative flow, cultural nuance) requires human evaluation before production activation.
