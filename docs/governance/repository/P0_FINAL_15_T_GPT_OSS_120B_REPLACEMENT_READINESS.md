# P0-FINAL-15-T: GPT-OSS 120B Replacement Readiness / Final Human-Gated Approval

## Baseline
- HEAD: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- Branch: main
- Timestamp: 2026-08-29T15:43:54.502644Z

## Candidate
- Model: openai/gpt-oss-120b
- Hosting: NVIDIA
- Endpoint: https://integrate.api.nvidia.com/v1/chat/completions

## Production State
- Production Model: minimaxai/minimax-m3
- Production State: FROZEN
- RM6 Status: BLOCKED

## Historical Evidence References
- P0_FINAL_15_R_CANDIDATE_EVALUATION.json
- P0_FINAL_15_S_FINAL_DECISION.json
- P0_FINAL_15_S_GPT_OSS_120B_CONTEXT_BOUNDARY_REPORT.json
- P0_FINAL_15_S_GPT_OSS_120B_TRANSLATION_QUALITY_REPORT.json
- P0_FINAL_15_S_GPT_OSS_120B_RELIABILITY_REPORT.json
- P0_FINAL_15_S_GPT_OSS_120B_RUNTIME_STABILITY_REPORT.json
- P0_FINAL_15_S1_GPT_OSS_120B_CONTEXT_QUALITY_RECOVERY_REPORT.json

## Gate Results

| Gate | Name | Result | Critical | Rationale |
|------|------|--------|----------|-----------|
| A | Provider Invocation | PASS | True | 3/3 attempts HTTP 200 |
| B | Runtime Stability | PASS | True | All 7 validated strategy calls HTTP 200 |
| C | Context Compatibility | PASS | True | Chunking: trunc=False, preserv=1.00; Budget: all_ok=True |
| D | Translation Quality | PASS | True | All fixtures >= 65: True |
| E | Glossary Effectiveness | PASS | True | Avg ΔQuality=+6.8, all fixtures improved: True |
| F | Continuity | FAIL | True | Repetition=False, ParaIntegrity=False, TermContinuity=1.00 |
| G | Reliability | PASS | True | Success rate: 100% (10/10), 429=0, 408=0, 5xx=0 |
| H | Human Literary Review | PENDING | True | Human review bundle exists but no result file found |
| I | Production Compatibility | PASS | True | All validated strategies compatible with existing production architecture |
| J | Governance | FAIL | True | ntpe_validate: FAIL, Root unexpected files: 8 |

## Final Decision

**BLOCKED_INSUFFICIENT_EVIDENCE**

## Validated Operating Envelope

### Primary Strategy
- **Name**: Chunking + Glossary
- **Description**: Split source into 3-4 chunks, translate each with glossary, reassemble

### Alternative Strategy
- **Name**: Output Budget 6000 + Glossary
- **Description**: Single request with max_tokens=6000 and glossary enforcement

## Risk Assessment
MEDIUM

## Production Freeze Verification
- **Verified**: True

## Limitations
- Single NVIDIA account used for all testing
- No cross-provider comparison performed
- Human literary review PENDING (bundle exists, result not yet submitted)
- Automated quality scoring is approximation; human review is authoritative
- Token estimation is character-based
- No sustained load testing
- No cross-region testing
- Production activation requires separate phase (P0-FINAL-15-U)

## Recommendation
Blocked on Human Literary Review (Gate H). Complete human review and re-run T phase.

---

> **Note**: This report certifies REPLACEMENT READINESS only. Actual production activation requires a separate phase (P0-FINAL-15-U).
