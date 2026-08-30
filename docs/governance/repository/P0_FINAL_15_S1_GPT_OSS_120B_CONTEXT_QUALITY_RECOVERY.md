# P0-FINAL-15-S1: GPT-OSS 120B Context & Quality Recovery Investigation

## Baseline
- HEAD: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- Branch: main
- Timestamp: 2026-08-29T14:51:17.544146Z

## Candidate
- Model: openai/gpt-oss-120b (NVIDIA)
- Production Model: minimaxai/minimax-m3 (FROZEN)
- RM6: BLOCKED

## Results

| Test | Fixture | Mode | Context | HTTP | Time | Trunc | Preserv | Quality | Pass |
|------|---------|------|---------|------|------|-------|---------|---------|------|
| CB_50 | narrative | glossary | 50% | 200 | 14.7s | True | 0.64 | 75.9 | True |
| CB_60 | narrative | glossary | 60% | 200 | 16.0s | True | 0.64 | 75.8 | True |
| CB_70 | narrative | glossary | 70% | 200 | 11.2s | True | 0.73 | 77.2 | True |
| CB_75 | narrative | glossary | 75% | 200 | 12.4s | True | 0.73 | 77.3 | True |
| CB_80 | narrative | glossary | 80% | 200 | 17.6s | True | 0.00 | 0.0 | False |
| CB_85 | narrative | glossary | 85% | 200 | 16.5s | False | 0.91 | 73.0 | True |
| CB_90 | narrative | glossary | 90% | 200 | 14.8s | True | 0.00 | 0.0 | False |
| CB_95 | narrative | glossary | 95% | 200 | 18.8s | True | 0.73 | 77.1 | True |
| CHUNK_single | narrative | glossary_chunked | 100% | 200 | 35.3s | True | 0.64 | 75.2 | True |
| CHUNK_small | narrative | glossary_chunked | 100% | 200 | 35.8s | False | 1.00 | 75.3 | True |
| CHUNK_medium | narrative | glossary_chunked | 100% | 200 | 38.6s | False | 1.00 | 75.1 | True |
| CHUNK_large | narrative | glossary_chunked | 100% | 200 | 29.9s | False | 1.00 | 74.5 | True |
| QUAL_narrative_base | narrative | base | 100% | 200 | 15.3s | False | 0.82 | 64.5 | False |
| QUAL_narrative_glossary | narrative | glossary | 100% | 200 | 20.7s | False | 1.00 | 74.6 | True |
| QUAL_dialogue_base | dialogue | base | 100% | 200 | 6.4s | False | 0.00 | 52.6 | False |
| QUAL_dialogue_glossary | dialogue | glossary | 100% | 200 | 9.9s | False | 1.00 | 72.4 | True |
| QUAL_continuity_base | continuity | base | 100% | 200 | 6.4s | False | 1.00 | 72.4 | True |
| QUAL_continuity_glossary | continuity | glossary | 100% | 200 | 6.5s | False | 0.92 | 72.7 | True |
| REDUCED_narrative_70 | narrative | glossary_reduced | 70% | 200 | 13.2s | True | 0.00 | 0.0 | False |
| REDUCED_narrative_80 | narrative | glossary_reduced | 80% | 200 | 13.1s | True | 0.00 | 0.0 | False |
| REDUCED_narrative_85 | narrative | glossary_reduced | 85% | 200 | 12.2s | True | 0.00 | 0.0 | False |
| BUDGET_narrative | narrative | glossary_budget | 100% | 200 | 21.5s | False | 0.91 | 74.4 | True |
| BUDGET_dialogue | dialogue | glossary_budget | 100% | 200 | 5.4s | False | 1.00 | 72.9 | True |
| BUDGET_continuity | continuity | glossary_budget | 100% | 200 | 8.3s | False | 1.00 | 72.6 | True |

## Classification

**RECOVERABLE**

## Human Review
PENDING (from P0-FINAL-15-S)

## Next Stage
Proceed to P0-FINAL-15-T if RECOVERABLE, otherwise remain on minimaxai/minimax-m3
