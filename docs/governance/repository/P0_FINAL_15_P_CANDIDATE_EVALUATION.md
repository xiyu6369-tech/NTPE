# P0-FINAL-15-P — NVIDIA Candidate Model Detailed Evaluation

## Baseline

- **HEAD**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **origin/main**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **divergence**: 0/0
- **branch**: main
- **Python**: 3.14.6
- **Endpoint**: https://integrate.api.nvidia.com/v1/chat/completions
- **Credential**: NVIDIA_API_KEY (present: True)
- **Timestamp**: 2026-08-29T05:31:47.146906Z

## Candidates Evaluated

- minimaxai/minimax-m3
- nvidia/llama-3.1-nemoguard-8b-content-safety
- nvidia/nemotron-3-nano-30b-a3b

## Evaluation Pipeline (Phases C-J)

### Phase C: Provider Smoke
5 controlled smoke observations per candidate.

### Phase D: Context Compatibility
4 context levels: small (~100 tokens), medium (~1K), large (~4K), high (~8K).

### Phase E: Raw Translation
3 fixtures (narrative, dialogue, continuity) in base mode.

### Phase F: NTPE-aware Translation
6 modes per fixture:
- Base
- + Glossary
- + Character Memory
- + Glossary + Character Memory
- + Previous Context
- + Glossary + Previous Context

### Phase G: Continuity
Assessed via translation results on continuity fixture.

### Phase H: Reliability
10 extended observations per candidate.

### Phase I: Quality Scoring
Automated scoring across 7 dimensions (minimum 65 for PASS).

### Phase J: Candidate Classification
Final classification per spec.

## Ranking (Section 22 Priority)

| Rank | Model | Score | Classification | Automated Pass | Reliability | Context | Quality |
|------|-------|-------|----------------|----------------|-------------|---------|---------|
| 1 | nvidia/llama-3.1-nemoguard-8b-content-safety | 79.41 | QUALITY_INSUFFICIENT | False | 100% | True | False |
| 2 | nvidia/nemotron-3-nano-30b-a3b | 70.57 | QUALITY_INSUFFICIENT | False | 100% | True | False |
| 3 | minimaxai/minimax-m3 | 0.0 | CONTEXT_INCOMPATIBLE | False | 0% | False | False |

## Detailed Results


### minimaxai/minimax-m3

**Classification**: CONTEXT_INCOMPATIBLE
**Rationale**: Failed context compatibility tests
**Overall Pass**: False

#### Phase C: Provider Smoke (5 observations)
- **Success Rate**: 0%
- **Median Latency**: 0ms
- **P95 Latency**: 0ms
- **HTTP 4xx**: 3
- **HTTP 408**: 0
- **HTTP 429**: 3
- **HTTP 5xx**: 0
- **Timeouts**: 0

#### Phase D: Context Compatibility
- **Compatible**: False
- **small**: HTTP 429 (180ms) - FAIL
- **medium**: HTTP 429 (198ms) - FAIL
- **large**: HTTP 429 (216ms) - FAIL

#### Phase E: Raw Translation (Base Mode)
- **Success Rate**: 0%
- **narrative**: HTTP 429 (197ms) - FAIL
- **dialogue**: HTTP 429 (165ms) - FAIL
- **continuity**: HTTP 429 (191ms) - FAIL

#### Phase F: NTPE-aware Translation

**narrative**:
- base: HTTP 429 (156ms) - FAIL
- glossary: HTTP 429 (173ms) - FAIL
- char_memory: HTTP 429 (189ms) - FAIL
- glossary_char_memory: HTTP 429 (168ms) - FAIL

**dialogue**:
- base: HTTP 429 (183ms) - FAIL
- glossary: HTTP 429 (149ms) - FAIL
- char_memory: HTTP 429 (159ms) - FAIL
- glossary_char_memory: HTTP 429 (179ms) - FAIL

**continuity**:
- base: HTTP 429 (185ms) - FAIL
- glossary: HTTP 429 (163ms) - FAIL
- char_memory: HTTP 429 (150ms) - FAIL
- glossary_char_memory: HTTP 429 (171ms) - FAIL

#### Phase H: Reliability (10 observations)
- **Success Rate**: {eval.reliability_success_rate:.0%}
- **Median Latency**: {eval.reliability_median_latency_ms:.0f}ms
- **P95 Latency**: {eval.reliability_p95_latency_ms:.0f}ms
- **HTTP 4xx**: {eval.reliability_http_4xx}
- **HTTP 408**: {eval.reliability_http_408}
- **HTTP 429**: {eval.reliability_http_429}
- **HTTP 5xx**: {eval.reliability_http_5xx}
- **Timeouts**: {eval.reliability_timeouts}

#### Phase I: Quality Scores

- **Automated Pass**: False

#### Phase J: Final Classification
- **Classification**: **CONTEXT_INCOMPATIBLE**
- **Rationale**: Failed context compatibility tests

---

### nvidia/llama-3.1-nemoguard-8b-content-safety

**Classification**: QUALITY_INSUFFICIENT
**Rationale**: Automated quality score < 65
**Overall Pass**: False

#### Phase C: Provider Smoke (5 observations)
- **Success Rate**: 100%
- **Median Latency**: 595ms
- **P95 Latency**: 603ms
- **HTTP 4xx**: 0
- **HTTP 408**: 0
- **HTTP 429**: 0
- **HTTP 5xx**: 0
- **Timeouts**: 0

#### Phase D: Context Compatibility
- **Compatible**: True
- **small**: HTTP 200 (607ms) - PASS
- **medium**: HTTP 200 (554ms) - PASS
- **large**: HTTP 200 (747ms) - PASS

#### Phase E: Raw Translation (Base Mode)
- **Success Rate**: 100%
- **narrative**: HTTP 200 (618ms) - PASS
- **dialogue**: HTTP 200 (605ms) - PASS
- **continuity**: HTTP 200 (436ms) - PASS

#### Phase F: NTPE-aware Translation

**narrative**:
- base: HTTP 200 (621ms) - PASS
- glossary: HTTP 200 (658ms) - PASS
- char_memory: HTTP 200 (645ms) - PASS
- glossary_char_memory: HTTP 200 (695ms) - PASS

**dialogue**:
- base: HTTP 200 (596ms) - PASS
- glossary: HTTP 200 (627ms) - PASS
- char_memory: HTTP 200 (604ms) - PASS
- glossary_char_memory: HTTP 200 (649ms) - PASS

**continuity**:
- base: HTTP 200 (602ms) - PASS
- glossary: HTTP 200 (603ms) - PASS
- char_memory: HTTP 200 (638ms) - PASS
- glossary_char_memory: HTTP 200 (626ms) - PASS

#### Phase H: Reliability (10 observations)
- **Success Rate**: {eval.reliability_success_rate:.0%}
- **Median Latency**: {eval.reliability_median_latency_ms:.0f}ms
- **P95 Latency**: {eval.reliability_p95_latency_ms:.0f}ms
- **HTTP 4xx**: {eval.reliability_http_4xx}
- **HTTP 408**: {eval.reliability_http_408}
- **HTTP 429**: {eval.reliability_http_429}
- **HTTP 5xx**: {eval.reliability_http_5xx}
- **Timeouts**: {eval.reliability_timeouts}

#### Phase I: Quality Scores
- **narrative_base**: Overall=20.1 (Semantic=10.1, Fluency=0.0, Style=0.0, Terminology=0.0, Character=0.0, Continuity=10.0, Format=0.0) - FAIL
- **dialogue_base**: Overall=21.6 (Semantic=11.6, Fluency=0.0, Style=0.0, Terminology=0.0, Character=0.0, Continuity=10.0, Format=0.0) - FAIL
- **continuity_base**: Overall=20.8 (Semantic=11.8, Fluency=0.0, Style=0.0, Terminology=0.0, Character=0.0, Continuity=5.0, Format=4.0) - FAIL
- **narrative_glossary**: Overall=20.1 (Semantic=10.1, Fluency=0.0, Style=0.0, Terminology=0.0, Character=0.0, Continuity=10.0, Format=0.0) - FAIL
- **narrative_char_memory**: Overall=20.1 (Semantic=10.1, Fluency=0.0, Style=0.0, Terminology=0.0, Character=0.0, Continuity=10.0, Format=0.0) - FAIL
- **narrative_glossary_char_memory**: Overall=20.1 (Semantic=10.1, Fluency=0.0, Style=0.0, Terminology=0.0, Character=0.0, Continuity=10.0, Format=0.0) - FAIL
- **dialogue_glossary**: Overall=21.6 (Semantic=11.6, Fluency=0.0, Style=0.0, Terminology=0.0, Character=0.0, Continuity=10.0, Format=0.0) - FAIL
- **dialogue_char_memory**: Overall=21.6 (Semantic=11.6, Fluency=0.0, Style=0.0, Terminology=0.0, Character=0.0, Continuity=10.0, Format=0.0) - FAIL
- **dialogue_glossary_char_memory**: Overall=21.6 (Semantic=11.6, Fluency=0.0, Style=0.0, Terminology=0.0, Character=0.0, Continuity=10.0, Format=0.0) - FAIL
- **continuity_glossary**: Overall=20.8 (Semantic=11.8, Fluency=0.0, Style=0.0, Terminology=0.0, Character=0.0, Continuity=5.0, Format=4.0) - FAIL
- **continuity_char_memory**: Overall=20.8 (Semantic=11.8, Fluency=0.0, Style=0.0, Terminology=0.0, Character=0.0, Continuity=5.0, Format=4.0) - FAIL
- **continuity_glossary_char_memory**: Overall=20.8 (Semantic=11.8, Fluency=0.0, Style=0.0, Terminology=0.0, Character=0.0, Continuity=5.0, Format=4.0) - FAIL

- **Automated Pass**: False

#### Phase J: Final Classification
- **Classification**: **QUALITY_INSUFFICIENT**
- **Rationale**: Automated quality score < 65

---

### nvidia/nemotron-3-nano-30b-a3b

**Classification**: QUALITY_INSUFFICIENT
**Rationale**: Automated quality score < 65
**Overall Pass**: False

#### Phase C: Provider Smoke (5 observations)
- **Success Rate**: 100%
- **Median Latency**: 1328ms
- **P95 Latency**: 1598ms
- **HTTP 4xx**: 0
- **HTTP 408**: 0
- **HTTP 429**: 0
- **HTTP 5xx**: 0
- **Timeouts**: 0

#### Phase D: Context Compatibility
- **Compatible**: True
- **small**: HTTP 200 (853ms) - PASS
- **medium**: HTTP 200 (21497ms) - PASS
- **large**: HTTP 200 (43510ms) - PASS

#### Phase E: Raw Translation (Base Mode)
- **Success Rate**: 100%
- **narrative**: HTTP 200 (26679ms) - PASS
- **dialogue**: HTTP 200 (1908ms) - PASS
- **continuity**: HTTP 200 (8352ms) - PASS

#### Phase F: NTPE-aware Translation

**narrative**:
- base: HTTP 200 (25694ms) - PASS
- glossary: HTTP 200 (27221ms) - PASS
- char_memory: HTTP 200 (27934ms) - PASS
- glossary_char_memory: HTTP 200 (25490ms) - PASS

**dialogue**:
- base: HTTP 200 (5003ms) - PASS
- glossary: HTTP 200 (10354ms) - PASS
- char_memory: HTTP 200 (7705ms) - PASS
- glossary_char_memory: HTTP 200 (14715ms) - PASS

**continuity**:
- base: HTTP 200 (8914ms) - PASS
- glossary: HTTP 200 (36159ms) - PASS
- char_memory: HTTP 200 (11017ms) - PASS
- glossary_char_memory: HTTP 200 (8072ms) - PASS

#### Phase H: Reliability (10 observations)
- **Success Rate**: {eval.reliability_success_rate:.0%}
- **Median Latency**: {eval.reliability_median_latency_ms:.0f}ms
- **P95 Latency**: {eval.reliability_p95_latency_ms:.0f}ms
- **HTTP 4xx**: {eval.reliability_http_4xx}
- **HTTP 408**: {eval.reliability_http_408}
- **HTTP 429**: {eval.reliability_http_429}
- **HTTP 5xx**: {eval.reliability_http_5xx}
- **Timeouts**: {eval.reliability_timeouts}

#### Phase I: Quality Scores
- **narrative_base**: Overall=59.5 (Semantic=10.9, Fluency=16.6, Style=10.0, Terminology=10.0, Character=0.0, Continuity=10.0, Format=2.0) - FAIL
- **dialogue_base**: Overall=53.3 (Semantic=14.6, Fluency=13.8, Style=10.0, Terminology=0.0, Character=0.0, Continuity=10.0, Format=5.0) - FAIL
- **continuity_base**: Overall=65.0 (Semantic=13.2, Fluency=18.0, Style=6.5, Terminology=12.3, Character=0.0, Continuity=10.0, Format=5.0) - FAIL
- **narrative_glossary**: Overall=69.5 (Semantic=10.9, Fluency=16.3, Style=10.0, Terminology=18.3, Character=0.0, Continuity=10.0, Format=4.0) - PASS
- **narrative_char_memory**: Overall=31.4 (Semantic=0.0, Fluency=3.0, Style=10.0, Terminology=8.3, Character=0.0, Continuity=10.0, Format=0.0) - FAIL
- **narrative_glossary_char_memory**: Overall=46.3 (Semantic=2.2, Fluency=4.1, Style=10.0, Terminology=20.0, Character=0.0, Continuity=10.0, Format=0.0) - FAIL
- **dialogue_glossary**: Overall=73.9 (Semantic=14.2, Fluency=14.7, Style=10.0, Terminology=20.0, Character=0.0, Continuity=10.0, Format=5.0) - PASS
- **dialogue_char_memory**: Overall=52.6 (Semantic=15.1, Fluency=13.5, Style=10.0, Terminology=0.0, Character=0.0, Continuity=10.0, Format=4.0) - FAIL
- **dialogue_glossary_char_memory**: Overall=70.3 (Semantic=11.8, Fluency=14.5, Style=10.0, Terminology=20.0, Character=0.0, Continuity=10.0, Format=4.0) - PASS
- **continuity_glossary**: Overall=35.2 (Semantic=0.0, Fluency=0.2, Style=0.0, Terminology=20.0, Character=0.0, Continuity=10.0, Format=5.0) - FAIL
- **continuity_char_memory**: Overall=67.2 (Semantic=13.6, Fluency=18.2, Style=6.5, Terminology=13.8, Character=0.0, Continuity=10.0, Format=5.0) - PASS
- **continuity_glossary_char_memory**: Overall=71.6 (Semantic=13.4, Fluency=18.2, Style=6.5, Terminology=18.5, Character=0.0, Continuity=10.0, Format=5.0) - PASS

- **Automated Pass**: False

#### Phase J: Final Classification
- **Classification**: **QUALITY_INSUFFICIENT**
- **Rationale**: Automated quality score < 65

---

## M1 Baseline (minimaxai/minimax-m3)


- **Classification**: CONTEXT_INCOMPATIBLE
- **Context Compatible**: False
- **Raw Translation Success**: 0%
- **Reliability Success**: 0%
- **Smoke 429 Rate**: 3/5
- **Reliability 429 Rate**: 5/10

## Limitations
- Token measurement uses character-based estimation
- Single-run per test condition (not repeated for statistical significance)
- Automated quality scoring is approximate; human review required for literary quality
- Glossary and character memory are simplified test versions
- Context tests use estimated tokens, not actual tokenizer counts
- Reliability tests limited to 10 observations
- No cross-chunk consistency testing
- Fixture set is limited (3 fixtures only)

## Compliance
- ✅ No credential leakage (only credential_source recorded)
- ✅ No retry policy modification
- ✅ No production behavior modification
- ✅ Root Hygiene compliant (tools/one_shots/)
- ✅ Protected Worktree not modified
- ✅ Historical evidence not modified
- ✅ No RPM limiter changes
- ✅ No concurrency/burst testing
- ✅ Production model (M1) unchanged

## Next Steps

1. **Human Review Bundle** creation for top candidates
2. **Governance Review** of evaluation results
3. **Controlled Canary** phase if REPLACEMENT_CANDIDATE identified
