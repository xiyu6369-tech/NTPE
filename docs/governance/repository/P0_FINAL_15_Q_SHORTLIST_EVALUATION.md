# P0-FINAL-15-Q — Shortlist Evaluation

## Phase Q7-Q9: Candidate Scoring, Preliminary Smoke, Early Translation Screen

### Baseline
- **HEAD**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **origin/main**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **divergence**: 0/0
- **branch**: main
- **Python**: 3.14.6
- **Endpoint**: https://integrate.api.nvidia.com/v1/chat/completions
- **Credential**: NVIDIA_API_KEY (present: True)
- **Timestamp**: 2026-08-29T06:06:58.913215Z

### Shortlist Selection
Top candidates from admission pool selected with diversity awareness.

| Model | Family | Admission Score |
|-------|--------|-----------------|
|  | nvidia | 100.0 |
|  | nvidia | 100.0 |
|  | deepseek-ai | 100.0 |
|  | google | 100.0 |
|  | meta | 100.0 |

## Q7: Candidate Scoring (from Admission)

| Model | Chinese | General LLM | Literary | Context | Multilingual | Instruction | Endpoint | Observability | Recent | Total |
|-------|---------|-------------|----------|---------|--------------|-------------|----------|---------------|--------|-------|
|  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0 |
|  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0 |
|  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0 |
|  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0 |
|  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0 |

## Q8: Preliminary Smoke Test

| Model | Observations | Success Rate | Median Latency | 429 Count | 408 Count |
|-------|--------------|--------------|----------------|-----------|-----------|
|  | 2 | 0% | 0ms | 0 | 0 |
|  | 2 | 0% | 0ms | 0 | 0 |
|  | 2 | 0% | 0ms | 0 | 0 |
|  | 2 | 0% | 0ms | 0 | 0 |
|  | 2 | 0% | 0ms | 0 | 0 |

## Q9: Early Translation Screen (Base + Glossary)

| Model | Fixture | Mode | Success | Latency | HTTP |
|-------|---------|------|---------|---------|------|
|  | narrative | base | False | 176ms | 400 |
|  | narrative | glossary | False | 189ms | 400 |
|  | dialogue | base | False | 177ms | 400 |
|  | dialogue | glossary | False | 154ms | 400 |
|  | continuity | base | False | 203ms | 400 |
|  | continuity | glossary | False | 147ms | 400 |
|  | narrative | base | False | 174ms | 400 |
|  | narrative | glossary | False | 177ms | 400 |
|  | dialogue | base | False | 162ms | 400 |
|  | dialogue | glossary | False | 146ms | 400 |
|  | continuity | base | False | 148ms | 400 |
|  | continuity | glossary | False | 178ms | 400 |
|  | narrative | base | False | 161ms | 400 |
|  | narrative | glossary | False | 164ms | 400 |
|  | dialogue | base | False | 166ms | 400 |
|  | dialogue | glossary | False | 158ms | 400 |
|  | continuity | base | False | 170ms | 400 |
|  | continuity | glossary | False | 190ms | 400 |
|  | narrative | base | False | 167ms | 400 |
|  | narrative | glossary | False | 159ms | 400 |
|  | dialogue | base | False | 180ms | 400 |
|  | dialogue | glossary | False | 175ms | 400 |
|  | continuity | base | False | 181ms | 400 |
|  | continuity | glossary | False | 186ms | 400 |
|  | narrative | base | False | 163ms | 400 |
|  | narrative | glossary | False | 171ms | 400 |
|  | dialogue | base | False | 130ms | 400 |
|  | dialogue | glossary | False | 173ms | 400 |
|  | continuity | base | False | 163ms | 400 |
|  | continuity | glossary | False | 154ms | 400 |

### Quality Screening Results

| Model | Avg Quality | Quality Pass | Glossary Improvement |
|-------|-------------|--------------|---------------------|
|  | 0.0 | False | +0.0 |
|  | 0.0 | False | +0.0 |
|  | 0.0 | False | +0.0 |
|  | 0.0 | False | +0.0 |
|  | 0.0 | False | +0.0 |

### Detailed Quality Scores


#### 

#### 

#### 

#### 

#### 

## Final Dispositions

| Model | Disposition | Rationale |
|-------|-------------|-----------|
|  | **EARLY_REJECTED** | Translation success rate 0% < 100% |
|  | **EARLY_REJECTED** | Translation success rate 0% < 100% |
|  | **EARLY_REJECTED** | Translation success rate 0% < 100% |
|  | **EARLY_REJECTED** | Translation success rate 0% < 100% |
|  | **EARLY_REJECTED** | Translation success rate 0% < 100% |

## Admitted to P0-FINAL-15-R

0 candidate(s):

## Early Rejected

5 candidate(s):
- : Translation success rate 0% < 100%
- : Translation success rate 0% < 100%
- : Translation success rate 0% < 100%
- : Translation success rate 0% < 100%
- : Translation success rate 0% < 100%

## Limitations
- Limited to 2 smoke observations per candidate
- Only 2 modes tested (base, glossary) per fixture
- Single-run per test condition
- Automated quality scoring is approximate
- Human literary review not performed
- Only 3 fixtures tested
- Glossary and character memory are simplified test versions

## Compliance
- ✅ No credential leakage
- ✅ No retry policy modification
- ✅ No production behavior modification
- ✅ Root Hygiene compliant (tools/one_shots/)
- ✅ Protected Worktree not modified
- ✅ Historical evidence not modified
- ✅ No RPM limiter changes
- ✅ No concurrency/burst testing
- ✅ Production model (M1) unchanged

## Next Phase

**P0-FINAL-15-R** — Controlled Candidate Evaluation for admitted candidates.
