# NTPE S7-08 — Literary Quality Evidence & Calibration Audit Report

**Audit Date**: 2026-09-30
**Auditor**: Kilo (Automated)
**Scope**: Evidence & Calibration Audit for Literary Quality per S7-08 mandate

---

## 1. Baseline

| Metric | Value |
|--------|-------|
| HEAD | `5b41e3d55b5d07f6e8d1fec2ea10fd83d22aedf5` ✓ |
| Branch | `main` ✓ |
| S7-07 Input Contract | `artifacts/NTPE_S7_07_LITERARY_QUALITY_CONTRACT_V1.md` |
| S7-07 Verdict | `S7_07_QUALITY_CONTRACT_V1_DEFINED_WITH_EXPLICIT_BOUNDARIES` |

### Working Tree (Pre-existing, Untouched)

| Category | Count |
|----------|-------|
| Modified (literary outputs) | 4 |
| Untracked (artifacts) | 25+ |

---

## 2. Input Contracts

**S7-07 Contract**: `QUALITY_CONTRACT_V1` — Deterministic production gates defined (14 gates), non-production areas explicitly bounded:
- Literary Naturalness → `OBSERVATIONAL_ONLY`
- PS-03 Aggregate → `OBSERVATIONAL_ONLY`
- Best Attempt Selection → `NOT_IMPLEMENTED`
- Segment Recovery Quality Merge → `NOT_IMPLEMENTED`
- Context Continuity → `FEATURE_GATED_OFF`
- Literary Reviewer/Editor/ACE → `NOT_IMPLEMENTED` / `TEST_ONLY`

---

## 3. Audit Scope

S7-08 audited evidence for promotion readiness of all non-production areas from S7-07:
1. Literary Naturalness (PS-03 Dimension 3)
2. PS-03 Six Dimensions & Aggregate
3. PS-03 Thresholds (80/65)
4. Human Evaluation Evidence
5. Reference Translation Evidence
6. Distribution / Statistical Evidence
7. False Positive / False Negative Evidence
8. Best Attempt Selection
9. Segment Recovery Quality Merge
10. Context Continuity
11. Literary Reviewer / Editor / ACE

---

## 4. Evidence Inventory

| Evidence Source | Type | Scope | Production Reachability |
|-----------------|------|-------|------------------------|
| `ntpe_literary_evaluation.py` | PS-03 Implementation | 6-dimension proxy scoring (100pt) | NO (post-hoc tooling) |
| `tests/literary/*/original_ko.txt` | Source Corpus | 3 test sets (Smoke, Golden, Regression) | NO |
| `tests/literary/outputs/*/original_ko_zh.txt` | Translation Outputs | Multiple stages, variable quality | NO |
| `Regression_History.json` | Historical Scores | 58 stages, scores 0-100 | NO |
| `best_attempt.py` + test | Best Attempt Logic | Unit test only | NOT_IMPLEMENTED (0 call sites) |
| `segment_recovery.py` | Segment Recovery | Env-gated, no production call | NOT_IMPLEMENTED |
| `adaptive_context_integration.py` + ACE tests | ACE | Test-only (disabled/shadow/active) | TEST_ONLY |
| `production_submission_adapter.py` | Context Continuity Flag | `quality_context_scene_v72=false` default | FEATURE_GATED_OFF |
| `evaluation.md` / `reference_notes.md` | Human Eval Guidance | Empty template + notes | NO human scores |

---

## 5. Evidence Quality Classification

| Evidence Item | Classification | Rationale |
|---------------|----------------|-----------|
| PS-03 proxy metrics (6 dims) | **C — Weak** | Heuristic proxies only; no calibration against human judgment |
| PS-03 weights (30/20/20/15/10/5) | **D — Non-evidence** | Arbitrary engineering choice; no empirical basis |
| PS-03 thresholds (80/65) | **D — Non-evidence** | Arbitrary design choice; no dataset validation |
| Literary source corpus (3 sets) | **B — Moderate** | Korean literary text available; no reference translations |
| Translation outputs (58 stages) | **C — Weak** | Machine outputs only; no human-labeled quality labels |
| Regression_History scores | **C — Weak** | Scores exist but unvalidated; 0-100 range from proxy |
| Best attempt test | **C — Weak** | Synthetic test data only; no real attempt quality labels |
| Segment recovery test | **D — Non-evidence** | No test for merge quality; only splitting logic tested |
| ACE tests | **D — Non-evidence** | Test scaffolding only; fallback logic tested |
| `evaluation.md` template | **D — Non-evidence** | Empty score template; no filled evaluations |
| `reference_notes.md` | **C — Weak** | Guidance notes only; no actual reference translations |

**No A (Strong) or B (Moderate) evidence found for literary quality calibration.**

---

## 6. Literary Naturalness Audit

| Aspect | Finding |
|--------|---------|
| **Definition** | "Natural Chinese proxy" — PS-03 Dimension 3 (20pts): korean_hits, chinese_density, preface_penalty |
| **Measurement** | Heuristic: `korean_penalty = min(12, korean_hits * 1.5)`, `density_penalty = 6 if chinese_density < 0.45`, `preface_penalty = 5` for machine prefaces |
| **Reference Data** | None — no human naturalness ratings |
| **Human Correlation** | **ABSENT** — No human evaluation study |
| **Calibration** | **NONE** — Thresholds (density≥0.45, korean_penalty cap) arbitrary |
| **Production Usage** | Post-hoc only (PS-03 tooling); not in pipeline |
| **Evidence Strength** | **C — Weak** (proxy only) |
| **Promotion Readiness** | **OBSERVATIONAL_ONLY** |

**Conclusion**: Literary Naturalness remains a heuristic proxy with no calibration basis. Cannot be promoted to HARD_GATE or SOFT_GATE.

---

## 7. PS-03 Dimension Audit

| Dimension | What It Measures | Evidence | Reference | Human Correlation | Threshold Basis | Status |
|-----------|------------------|----------|-----------|-------------------|-----------------|--------|
| **Plot Fidelity Proxy** (30pts) | Length ratio of translation vs source | Length ratio heuristic | No reference translation | ABSENT | Arbitrary (0.18/0.35 cutoffs) | **OBSERVATIONAL** |
| **Locked Names/Terms** (20pts) | Exact match of 4 locked terms + forbidden variants | Deterministic string matching | Locked terms defined in code | N/A (deterministic) | Zero tolerance | **HARD_GATE** (already production) |
| **Natural Chinese Proxy** (20pts) | Korean residue, Chinese density, preface detection | Heuristic proxy | None | ABSENT | Arbitrary (density≥0.45, korean_penalty=1.5×hits) | **OBSERVATIONAL** |
| **Subject/Pronoun Proxy** (15pts) | Demonstrative repetition + known Kyle error | Heuristic pattern matching | None | ABSENT | Arbitrary (0.8×repetition, 8pt Kyle penalty) | **OBSERVATIONAL** |
| **Character Voice/Dialogue** (10pts) | Dialogue punctuation `「」` count vs source | Deterministic count | None | ABSENT | Arbitrary (≥2 = pass, else 4pts) | **LOCAL_REPAIR** (already production) |
| **Format/Punctuation** (5pts) | Simplified Chinese hint chars | Deterministic char set check | None | N/A (deterministic) | Zero tolerance | **HARD_GATE** (already production) |

**Key Finding**: Only 2 of 6 dimensions (Locked Terms, Format/Punctuation) have deterministic measurement suitable for production gates. The other 4 are heuristic proxies with **no human correlation evidence**.

---

## 8. PS-03 Aggregate Calibration Audit

| Aspect | Finding |
|--------|---------|
| **Aggregate Formula** | Simple sum of 6 dimension scores (max 100) |
| **Weights** | 30/20/20/15/10/5 — **Arbitrary engineering choice**; no empirical justification |
| **Thresholds** | ≥80 = success, ≥65 = warning, <65 = failed — **Arbitrary**; no dataset validation |
| **Dimension Interaction** | Simple additive; no correlation analysis between dimensions |
| **False Positive Analysis** | **ABSENT** — No known-good/bad labeled data |
| **False Negative Analysis** | **ABSENT** |
| **Score Distribution** | Historical: 0-100 across 58 stages; bimodal (0/95+) due to missing outputs |
| **Production Correlation** | **ABSENT** — PS-03 never used in production acceptance |

**Conclusion**: PS-03 aggregate is **NOT CALIBRATED**. Weights and thresholds have **zero evidence basis**. Remains `OBSERVATIONAL_ONLY`.

---

## 9. Threshold 80/65 Audit

| Threshold | Source | Empirical Basis | Dataset | False Positive Rate | False Negative Rate |
|-----------|--------|-----------------|---------|---------------------|---------------------|
| **80 (success)** | `ntpe_literary_evaluation.py:174` | **NONE** — arbitrary | None | UNKNOWN | UNKNOWN |
| **65 (warning)** | `ntpe_literary_evaluation.py:174` | **NONE** — arbitrary | None | UNKNOWN | UNKNOWN |

**Origin**: Engineering design choice in PS-03 implementation. No calibration study, no human evaluation dataset, no ROC analysis.

**Verdict**: **UNCALIBRATED** — Cannot be used as production acceptance thresholds.

---

## 10. Human Evaluation Evidence

| Evidence Type | Status | Details |
|---------------|--------|---------|
| **Expert Annotations** | **ABSENT** | No human evaluator data |
| **Pairwise Comparisons** | **ABSENT** | No A/B testing |
| **Likert/Scale Ratings** | **ABSENT** | No human scoring |
| **Inter-rater Agreement** | **ABSENT** | No multiple evaluators |
| **Adjudication Process** | **ABSENT** | No disagreement resolution |
| **Evaluation Instructions** | **PARTIAL** | `evaluation.md` template exists but **empty**; `reference_notes.md` has guidance only |
| **Filled Evaluations** | **ABSENT** | No completed evaluation sheets found |

**Conclusion**: **NO HUMAN EVALUATION EVIDENCE EXISTS**. Cannot calibrate literary quality metrics against human judgment.

---

## 11. Reference Translation Evidence

| Evidence Type | Status | Details |
|---------------|--------|---------|
| **Professional Human Translations** | **ABSENT** | No professionally translated reference corpus |
| **Human-Reviewed Outputs** | **ABSENT** | No machine outputs reviewed/edited by humans |
| **Gold Standard Fixtures** | **PARTIAL** | Source texts exist (`original_ko.txt`); **no reference translations (`original_ko_zh.txt`)** in test sets |
| **Machine Outputs as Reference** | **PRESENT** | PS-03-integration-minimax outputs exist but are **machine-generated**, not human-validated |
| **Reference Provenance** | **N/A** | No human reference to establish provenance |

**Key Distinction**: The repository contains **source texts only** (`original_ko.txt`). The `original_ko_zh.txt` files in outputs are **machine translations**, not human references. No gold-standard literary translation corpus exists.

---

## 12. Distribution / Statistical Evidence

| Analysis | Status | Findings |
|----------|--------|----------|
| **Score Distribution** | **PARTIAL** | 58 stages in Regression_History; bimodal (0 or 95+); most "failed" due to missing outputs |
| **Dimension Distribution** | **ABSENT** | No per-dimension statistical analysis |
| **Correlation Analysis** | **ABSENT** | No dimension-dimension or dimension-human correlation |
| **Threshold Hit Rate** | **PARTIAL** | Most stages 0 (missing output) or 95+ (success); 80/65 thresholds untested on real distribution |
| **Variance/Stability** | **ABSENT** | No repeated measures or stability analysis |

**Conclusion**: Insufficient statistical evidence for calibration. Bimodal distribution driven by pipeline execution (missing output = 0), not literary quality variance.

---

## 13. False Positive / False Negative Evidence

| Metric | False Positive Evidence | False Negative Evidence |
|--------|------------------------|------------------------|
| PS-03 Naturalness | **UNKNOWN** — No human labels | **UNKNOWN** |
| PS-03 Aggregate | **UNKNOWN** | **UNKNOWN** |
| Best Attempt Ranking | **UNKNOWN** — No human preference data | **UNKNOWN** |
| Segment Merge Quality | **UNKNOWN** — No merge test data | **UNKNOWN** |

**Cannot estimate FP/FN rates without human-validated ground truth.**

---

## 14. Best Attempt Selection Audit

| Aspect | Finding |
|--------|---------|
| **Implementation** | `core/translation_quality_v5/best_attempt.py` — `select_best_attempt()` with deterministic ranking |
| **Ranking Algorithm** | 5-tuple: (decision_rank, score, -blocking_issues, -issue_count, translation_length) |
| **Production Call Sites** | **ZERO** — `Select-String` returns no production invocations |
| **Test Evidence** | `archive/stage_tests/ntpe_te_v5531_completeness_recovery_best_attempt_test.py` — **Synthetic data only** (hardcoded QA reports) |
| **Attempt Quality Labels** | **ABSENT** — No real attempt quality labels; no human preference between attempts |
| **Cross-Attempt Normalization** | **UNDEFINED** — Scores not comparable across attempts (different chunks = different baselines) |
| **Quality Floor** | **UNDEFINED** |
| **Tie Handling** | Deterministic (max by rank tuple) but no evidence it matches human preference |

**Conclusion**: **NOT_IMPLEMENTED** in production; **NOT_CALIBRATABLE_YET** — No attempt-level quality labels, no human preference data, no cross-attempt score normalization.

---

## 15. Segment Recovery Quality Merge Audit

| Aspect | Finding |
|--------|---------|
| **Segmentation Logic** | `segment_recovery.py` — Conservative splitting (paragraph → sentence → char) |
| **Trigger** | `NTPE_SEGMENT_COMPLETENESS_RECOVERY` env var + source ≥360 chars + completeness issues |
| **Production Call Sites** | **ZERO** — Env-gated but not connected to pipeline |
| **Merge Logic** | **NOT_IMPLEMENTED** — No segment result merging, ordering, duplicate prevention |
| **Boundary Integrity** | **UNTESTED** — No tests for cross-segment contamination or ordering failures |
| **Segment Quality Labels** | **ABSENT** — No segment-level quality measurements |
| **Human Acceptance** | **ABSENT** — No human evaluation of merged outputs |

**Conclusion**: **NOT_IMPLEMENTED** in production; **NOT_CALIBRATABLE_YET** — No merge strategy, no quality evidence, no boundary integrity tests.

---

## 16. Context Continuity Audit

| Aspect | Finding |
|--------|---------|
| **Flag** | `quality_context_scene_v72: bool = False` (default) in `production_submission_adapter.py:38` |
| **Integration** | `translation_engine.py:70` reads flag from package metadata; applies TQI V72 if enabled |
| **Default State** | **OFF** — Explicit opt-in required via metadata |
| **Evidence for Quality Gain** | **ABSENT** — No context-on vs context-off comparison; no continuity error measurements |
| **Human Preference** | **ABSENT** |
| **Controlled Benchmark** | **ABSENT** |
| **Production Activation** | **NONE** — No production path enables it |

**Conclusion**: **FEATURE_GATED_OFF** — No evidence supports promotion. Cannot enable without controlled benchmark.

---

## 17. Literary Reviewer / Editor / ACE Audit

| Component | Status | Evidence | Production Reachability |
|-----------|--------|----------|------------------------|
| **ACE (Adaptive Context Engine)** | **TEST_ONLY** | Tests only: `mode='disabled'|'shadow'|'active'` with fallback logic; no production integration | NO |
| **Literary Reviewer** | **NOT_IMPLEMENTED** | Zero repository evidence (no class, prompt, fixture) | NO |
| **Literary Editor** | **NOT_IMPLEMENTED** | Zero repository evidence | NO |

**ACE Detail**: Tests only verify fallback behavior (`used_ace` vs `fallback_used`). No quality effect measurement. No production code path calls ACE.

---

## 18. Promotion Readiness Matrix

| Area | Current Status | Evidence Found | Evidence Strength | Calibration Basis | Production Ready | Next Evidence Needed |
|------|----------------|----------------|-------------------|-------------------|------------------|---------------------|
| **Literary Naturalness** | OBSERVATIONAL_ONLY | PS-03 proxy (20pts) | C (Weak) | NONE | NO | Human naturalness ratings; calibration dataset |
| **PS-03 Dimensions (4 heuristic)** | OBSERVATIONAL_ONLY | Proxy implementations | C (Weak) | NONE | NO | Human correlation study; deterministic alternatives |
| **PS-03 Dimensions (2 deterministic)** | HARD_GATE/LOCAL_REPAIR | Deterministic string matching | A (Strong for these) | DIRECT | YES (already) | N/A |
| **PS-03 Aggregate** | OBSERVATIONAL_ONLY | 100pt sum | D (Non-evidence) | NONE | NO | Weight calibration; threshold validation; FP/FN analysis |
| **Threshold 80/65** | UNCALIBRATED | Arbitrary constants | D (Non-evidence) | NONE | NO | ROC analysis on labeled data; human agreement |
| **Best Attempt Selection** | NOT_IMPLEMENTED | Synthetic test only | C (Weak) | NONE | NO | Attempt quality labels; human preference data; cross-attempt normalization |
| **Segment Recovery Merge** | NOT_IMPLEMENTED | Segmentation only | D (Non-evidence) | NONE | NO | Merge strategy; segment quality labels; boundary tests |
| **Context Continuity** | FEATURE_GATED_OFF | Flag exists, default off | D (Non-evidence) | NONE | NO | Context-on/off benchmark; continuity error corpus |
| **Literary Reviewer** | NOT_IMPLEMENTED | NONE | D (Non-evidence) | N/A | NO | Component implementation; evaluation protocol |
| **Literary Editor** | NOT_IMPLEMENTED | NONE | D (Non-evidence) | N/A | NO | Component implementation; edit operation definition |
| **ACE** | TEST_ONLY | Test scaffolding | D (Non-evidence) | NONE | NO | Production integration; quality effect measurement |

---

## 19. Required Future Evidence (For Any Promotion)

To promote any area to production contract, **minimum evidence required**:

| Requirement | Literary Naturalness | PS-03 Aggregate | Best Attempt | Segment Merge | Context Continuity |
|-------------|---------------------|-----------------|--------------|---------------|-------------------|
| Source Corpus | ✅ (3 sets) | ✅ | ❌ | ✅ | ✅ |
| Reference Translation | ❌ | ❌ | ❌ | ❌ | ❌ |
| Human Evaluation Rubric | ❌ | ❌ | ❌ | ❌ | ❌ |
| Multiple Evaluators | ❌ | ❌ | ❌ | ❌ | ❌ |
| Dimension-Level Labels | ❌ | ❌ | ❌ | ❌ | ❌ |
| Aggregate Labels | ❌ | ❌ | ❌ | ❌ | ❌ |
| Known Failure Cases | ❌ | ❌ | ❌ | ❌ | ❌ |
| Threshold Selection Method | ❌ | ❌ | ❌ | ❌ | ❌ |
| Validation Set | ❌ | ❌ | ❌ | ❌ | ❌ |
| Holdout Set | ❌ | ❌ | ❌ | ❌ | ❌ |
| FP/FN Analysis | ❌ | ❌ | ❌ | ❌ | ❌ |
| Repeatability Check | ❌ | ❌ | ❌ | ❌ | ❌ |

**All critical evidence missing.**

---

## 20. Production Boundary Verification

| Boundary | Status | Evidence |
|----------|--------|----------|
| **Model Frozen** | ✅ PASS | `meta/llama-3.2-90b-vision-instruct` (all 9 config files) |
| **Provider Frozen** | ✅ PASS | `nvidia` |
| **Retry Boundary** | ✅ PASS | Max 5 attempts; provider switch after 3; chunk halving for quality failures |
| **Quality Gates Preserved** | ✅ PASS | All 14 deterministic gates unchanged |
| **Real Translation** | ✅ 0 | No provider calls in audit |
| **Network Execution** | ✅ 0 | No network calls in audit |
| **Production Files Modified** | ✅ NO | 0 production files changed |
| **Context Feature** | ✅ OFF | `quality_context_scene_v72=false` default unchanged |
| **Root Hygiene** | ✅ PASS | No root scratch files |

---

## 21. Regression Tests

| Suite | Before | After | Status |
|-------|--------|-------|--------|
| S6-02 TXT Success/Failure | 6/6 | 6/6 | ✅ PASS |
| S6-03 EPUB | 7/7 | 7/7 | ✅ PASS |
| S6-04 Validation | 16/16 | 16/16 | ✅ PASS |
| S6-05 Dry-Run | 8/8 | 8/8 | ✅ PASS |
| **Total** | **37/37** | **37/37** | ✅ **ALL PASS** |

---

## 22. Undefined / Uncalibrated Areas (Explicit)

| Area | Status | Reason |
|------|--------|--------|
| Literary Naturalness | UNCALIBRATED | No human correlation; heuristic proxy only |
| PS-03 Aggregate | UNCALIBRATED | Arbitrary weights/thresholds; no validation |
| PS-03 Thresholds (80/65) | UNCALIBRATED | Arbitrary constants; no ROC analysis |
| Best Attempt Selection | NOT_IMPLEMENTED | 0 production call sites; no attempt quality labels |
| Segment Recovery Merge | NOT_IMPLEMENTED | No merge logic; no quality evidence |
| Context Continuity | FEATURE_GATED_OFF | Default off; no benchmark evidence |
| Literary Reviewer | NOT_IMPLEMENTED | Zero repository evidence |
| Literary Editor | NOT_IMPLEMENTED | Zero repository evidence |
| ACE | TEST_ONLY | Test scaffolding only; no production path |

---

## 23. Final Verdict

```
S7_08_LITERARY_QUALITY_REMAINS_OBSERVATIONAL_ONLY
```

### Rationale

**No non-production area has sufficient evidence for promotion to production contract.**

- **Literary Naturalness**: Heuristic proxy (PS-03) with no human correlation → `OBSERVATIONAL_ONLY`
- **PS-03 Aggregate**: 100-point sum with arbitrary weights (30/20/20/15/10/5) and uncalibrated thresholds (80/65) → `OBSERVATIONAL_ONLY`
- **Best Attempt Selection**: Function exists but **0 production call sites**; no attempt quality labels, no human preference data, no cross-attempt normalization → `NOT_IMPLEMENTED`
- **Segment Recovery Merge**: Segmentation logic exists but **no merge strategy, no quality evidence, no boundary tests** → `NOT_IMPLEMENTED`
- **Context Continuity**: Flag explicitly default `False`; no controlled benchmark evidence → `FEATURE_GATED_OFF`
- **Literary Reviewer/Editor**: Zero repository evidence → `NOT_IMPLEMENTED`
- **ACE**: Test-only scaffolding with fallback logic; no quality effect measurement → `TEST_ONLY`

**Only the 2 deterministic dimensions (Locked Terms, Format/Punctuation) and 1 LOCAL_REPAIR (Dialogue Quotes) meet production gate standards — already integrated per S7-07.**

---

## 24. Compliance Summary

| Requirement | Status |
|-------------|--------|
| S7-07 contract consumed | ✅ YES |
| All non-production areas audited | ✅ YES |
| Evidence provenance documented | ✅ YES |
| Evidence strength classified (A/B/C/D) | ✅ YES |
| PS-03 six dimensions audited | ✅ YES |
| PS-03 aggregate weights audited | ✅ YES |
| Threshold 80/65 audited | ✅ YES |
| Human evaluation evidence audited | ✅ YES (ABSENT) |
| Reference translation evidence audited | ✅ YES (ABSENT) |
| FP/FN evidence audited | ✅ YES (UNKNOWN) |
| Best Attempt evidence audited | ✅ YES (NOT_CALIBRATABLE) |
| Segment Recovery evidence audited | ✅ YES (NOT_CALIBRATABLE) |
| Context Continuity audited (feature off) | ✅ YES |
| Reviewer/Editor/ACE evidence audited | ✅ YES |
| No arbitrary threshold introduced | ✅ YES |
| No production gate promoted without evidence | ✅ YES |
| No production behavior changed | ✅ YES |
| Retry boundary preserved | ✅ YES |
| Model/provider preserved | ✅ YES |
| Real translation = 0 | ✅ YES |
| Provider/network = 0 | ✅ YES |
| Regression contracts preserved | ✅ YES (37/37) |
| Pre-existing changes preserved | ✅ YES |
| Root hygiene preserved | ✅ YES |
| Promotion matrix completed | ✅ YES |

---

*End of Audit Report*

**Report Path**: `artifacts/NTPE_S7_08_LITERARY_QUALITY_EVIDENCE_CALIBRATION_AUDIT_REPORT.md`
**Audit Complete**: `S7_08_LITERARY_QUALITY_REMAINS_OBSERVATIONAL_ONLY`