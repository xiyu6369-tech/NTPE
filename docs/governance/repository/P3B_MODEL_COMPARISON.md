# P3B_MODEL_COMPARISON — Phase 3B Controlled Golden Set / Literary Model Comparison

## Baseline
- **HEAD**: `af5cbc091424849134c28ef931ce78d31ea0dc7d`
- **Identity**: PRE-MINIMAX-RECONSTRUCTED-BASELINE
- **Timestamp**: 2026-08-30T15:39:45.528734Z

## Candidates

- **M3 - Llama 3.2 90B Vision**: `meta/llama-3.2-90b-vision-instruct` (Vision LLM)
- **M4 - Riva Translate 4B v2**: `nvidia/riva-translate-4b-instruct-v2` (Translation Model)

## Golden Set Manifest
- **Manifest ID**: P3B_GOLDEN_SET_20260830_153351
- **Fixtures**: 18
  - GOLDEN_001: Golden_Set_Novel_Main (narrative) - 2476 chars - hash:04132a4c761a7592
  - SMOKE_001: Smoke_Set_Short (narrative) - 455 chars - hash:ee1822ba1ce56c6e
  - REGRESSION_001: Regression_Set_Novel (narrative) - 3078 chars - hash:754b85304ccd1b5b
  - DIALOGUE_001: Dialogue_Heavy_Scene (dialogue) - 323 chars - hash:2e065203ec7d3642
  - CONTEXT_001: Character_Continuity_Detectives (context_continuity) - 283 chars - hash:56f63e98108819fe
  - GLOSSARY_001: Glossary_Terms_Wuxia (glossary) - 133 chars - hash:dabd2b9a0e517958
  - LONG_01: Longitudinal_Chapter_1 (longitudinal) - 6 chars - hash:ad72257ccd7aeb40
  - LONG_02: Longitudinal_Chapter_2 (longitudinal) - 157 chars - hash:a871be017102686d
  - LONG_03: Longitudinal_Chapter_3 (longitudinal) - 7 chars - hash:27b9cced40fbb5cf
  - LONG_04: Longitudinal_Chapter_4 (longitudinal) - 114 chars - hash:f6de5ed0679c3038
  - LONG_05: Longitudinal_Chapter_5 (longitudinal) - 6 chars - hash:92c2472fb4187fe6
  - LONG_06: Longitudinal_Chapter_6 (longitudinal) - 106 chars - hash:5c404b2d5b454900
  - LONG_07: Longitudinal_Chapter_7 (longitudinal) - 6 chars - hash:775d3855af750885
  - LONG_08: Longitudinal_Chapter_8 (longitudinal) - 109 chars - hash:12014e6d8d60c5d9
  - LONG_09: Longitudinal_Chapter_9 (longitudinal) - 6 chars - hash:53752c26be6a4a66
  - LONG_10: Longitudinal_Chapter_10 (longitudinal) - 104 chars - hash:1db43c930be6e5f4
  - LONG_11: Longitudinal_Chapter_11 (longitudinal) - 6 chars - hash:e884462509c6bb2b
  - LONG_12: Longitudinal_Chapter_12 (longitudinal) - 143 chars - hash:f88482de88e2aeca

## Comparison Matrix

| Dimension | M3 | M4 | Winner |
|-----------|----|----|--------|
| Completion | 100.0 | 38.9 | M3 |
| Semantic Fidelity | 84.7 | 94.3 | M4 |
| Literary Quality | 66.7 | 0.0 | M3 |
| Traditional Chinese | 91.2 | 100.0 | M4 |
| Character Consistency | 94.4 | 85.7 | M3 |
| Context Continuity | 94.4 | 85.7 | M3 |
| Glossary | 35.8 | 4.1 | M3 |
| Structural Compliance | 86.7 | 80.0 | M3 |
| Timeout Rate | 0.0 | 0.0 | TIE |
| Retry Burden | 0.0 | 0.0 | TIE |
| Runtime (Avg Latency ms) | 19197.0 | 483.0 | M4 |
| Production Suitability | 92.0 | 66.9 | M3 |

## Production Suitability Classification

- **M3 (M3 - Llama 3.2 90B Vision)**: PRODUCTION_CANDIDATE
- **M4 (M4 - Riva Translate 4B v2)**: INCOMPATIBLE

## Quality Scores (Aggregate)

| Dimension | M3 | M4 |
|-----------|----|----|
| Semantic Fidelity | 84.7 | 94.3 |
| Literary Quality | 66.7 | 0.0 |
| Trad Chinese Quality | 91.2 | 100.0 |
| Character Consistency | 94.4 | 85.7 |
| Context Continuity | 94.4 | 85.7 |
| Terminology Glossary | 35.8 | 4.1 |
| Structural Compliance | 86.7 | 80.0 |
| Overall Quality | 80.0 | 63.0 |

## Runtime Metrics

| Metric | M3 | M4 |
|--------|----|----|
| Total Requests | 18 | 18 |
| Successful | 18 | 7 |
| Failed | 0 | 11 |
| Completion Rate | 100.0% | 38.9% |
| Timeouts (408) | 0 | 0 |
| Rate Limited (429) | 0 | 0 |
| 4xx Errors | 0 | 11 |
| 5xx Errors | 0 | 0 |
| Network Errors | 0 | 0 |
| Retries | 0 | 0 |
| Empty Outputs | 0 | 11 |
| Total Runtime | 345.5s | 8.7s |
| Avg Latency | 19197ms | 483ms |

## Phase Verdict
**P3B_CLEAR_WINNER**

## Critical Findings
- M4: 11 failed requests
- Quality Winner: M3 (M3:80.0 vs M4:63.0)
- Stability Winner: M4
- Production Candidate: M3

## Artifacts
- main_report: `artifacts/p3b_model_comparison/P3B_MODEL_COMPARISON_REPORT.json`
- scorecard: `artifacts/p3b_model_comparison/P3B_MODEL_SCORECARD.json`
- manifest: `artifacts/p3b_model_comparison/P3B_GOLDEN_SET_MANIFEST.json`
- governance: `docs/governance/repository/P3B_MODEL_COMPARISON.md`

## Repository Integrity
**PASS**

## Phase Boundary
**Phase 3B COMPLETE — STOP**

Do NOT:
- Modify default model
- Modify provider config
- Modify prompt
- Modify runtime
- Commit
- Push

Next: Human review of P3B evidence for migration decision.