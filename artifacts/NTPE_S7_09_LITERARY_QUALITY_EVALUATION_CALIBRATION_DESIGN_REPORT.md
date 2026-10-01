# NTPE S7-09 — Literary Quality Evaluation & Calibration Design Report

**Design Date**: 2026-09-30
**Author**: Kilo (Automated)
**Scope**: Evaluation & Calibration Framework Design per S7-09 mandate

---

## 1. Baseline

| Metric | Value |
|--------|-------|
| HEAD | `5b41e3d55b5d07f6e8d1fec2ea10fd83d22aedf5` ✓ |
| Branch | `main` ✓ |
| Model | `meta/llama-3.2-90b-vision-instruct` (FROZEN) |
| Provider | `nvidia` (FROZEN) |
| S7-07 Contract | `QUALITY_CONTRACT_V1` (LOCKED) |
| S7-08 Verdict | `S7_08_LITERARY_QUALITY_REMAINS_OBSERVATIONAL_ONLY` |

### Working Tree (Pre-existing, Untouched)

| Category | Count |
|----------|-------|
| Modified (literary outputs) | 4 |
| Untracked (artifacts) | 25+ |

---

## 2. Input Artifacts Consumed

| Artifact | Path | Status |
|----------|------|--------|
| S7-07 Contract | `artifacts/NTPE_S7_07_LITERARY_QUALITY_CONTRACT_V1.md` | ✅ CONSUMED |
| S7-07 Report | `artifacts/NTPE_S7_07_LITERARY_QUALITY_CONTRACT_V1_REPORT.md` | ✅ CONSUMED |
| S7-08 Audit | `artifacts/NTPE_S7_08_LITERARY_QUALITY_EVIDENCE_CALIBRATION_AUDIT_REPORT.md` | ✅ CONSUMED |

---

## 3. S7-08 Evidence Summary

| Area | S7-08 Status | Evidence Strength | Calibration Basis |
|------|--------------|-------------------|-------------------|
| Literary Naturalness | OBSERVATIONAL_ONLY | C (Weak) | NONE |
| PS-03 Heuristic Dimensions | OBSERVATIONAL_ONLY | C (Weak) | NONE |
| PS-03 Deterministic Dimensions | HARD_GATE/LOCAL_REPAIR | A (Strong) | DIRECT (already production) |
| PS-03 Aggregate | OBSERVATIONAL_ONLY | D (Non-evidence) | NONE |
| Thresholds 80/65 | UNCALIBRATED | D (Non-evidence) | NONE |
| Best Attempt Selection | NOT_IMPLEMENTED | C (Weak - synthetic) | NONE |
| Segment Recovery Merge | NOT_IMPLEMENTED | D (Non-evidence) | NONE |
| Context Continuity | FEATURE_GATED_OFF | D (Non-evidence) | NONE |
| Literary Reviewer/Editor | NOT_IMPLEMENTED | D (Non-evidence) | N/A |
| ACE | TEST_ONLY | D (Non-evidence) | NONE |

**Key Finding**: No A/B evidence exists for literary quality calibration. All promotion pathways blocked by evidence gaps.

---

## 4. Design Scope

S7-09 designed a complete **evidence acquisition → evaluation → calibration → validation → promotion** framework for all 10 non-production areas from S7-07/S7-08:

| Area | Design Status |
|------|---------------|
| Evaluation Corpus | ✅ DEFINED |
| Sampling Strategy | ✅ DEFINED |
| Translation Candidates | ✅ DEFINED |
| Reference Translation Policy | ✅ DEFINED |
| Human Evaluation Rubric | ✅ DEFINED (7 dimensions, 7-pt Likert + binary) |
| Human Evaluation Protocol | ✅ DEFINED (blind, randomized, fatigue-controlled) |
| Pairwise Evaluation | ✅ DEFINED (for Best Attempt, Segment, Context, ACE) |
| Inter-Rater Agreement | ✅ DEFINED (weighted κ, ICC, Bradley-Terry) |
| PS-03 Calibration | ✅ DEFINED (Spearman ρ, isotonic regression, weight optimization) |
| Aggregate Calibration | ✅ DEFINED (constrained optimization, 5-fold CV) |
| Threshold Calibration | ✅ DEFINED (Youden, cost-sensitive, ROC/PR) |
| Validation/Holdout Split | ✅ DEFINED (60/20/20, chapter-level) |
| Leakage Prevention | ✅ DEFINED (chapter/scene/passage/candidate deduplication) |
| FP/FN Analysis | ✅ DEFINED (3:1 cost ratio, per-dimension) |
| Best Attempt Design | ✅ DEFINED (pairwise blind, rank correlation) |
| Segment Recovery Design | ✅ DEFINED (segment-level + merge strategies) |
| Context Continuity Design | ✅ DEFINED (blind A/B, dimension scores) |
| Reviewer/Editor/ACE Design | ✅ DEFINED (blind baseline vs processed) |
| Cost/Value Assessment | ✅ DEFINED (3:1 FP:FN cost, net value rule) |
| Dataset Schema | ✅ DEFINED (5 core tables, 60+ fields) |
| Versioning/Reproducibility | ✅ DEFINED (semantic versioning, full reproducibility pkg) |
| Pilot Study | ✅ DEFINED (50 passages, 3-5 evaluators, Go/No-Go) |
| Stopping Criteria | ✅ DEFINED (stable validation, cost cap, agreement floor) |
| Promotion Criteria | ✅ DEFINED (10 mandatory criteria, ALL required) |

---

## 5. Key Design Decisions

### 5.1 Evaluation Unit: Scene-Level Passage
Multi-paragraph context window (500-3000 chars) matching LTS chunking and EPUB chapter structure.

### 5.2 Primary Evaluation Method: Blind Absolute + Pairwise
- **Absolute**: 7-dimension Likert (1-7) + binary ACCEPT/REJECT + failure tags
- **Pairwise**: Blind A vs B for Best Attempt, Segment Merge, Context, ACE

### 5.3 Inter-Rater Agreement: Weighted Cohen's Kappa (κw)
| Level | κw | Action |
|-------|-----|--------|
| Excellent | ≥0.80 | Ready |
| Good | 0.60-0.79 | Acceptable |
| Moderate | 0.40-0.59 | Revise rubric |
| Poor | <0.40 | Abandon |

### 5.4 PS-03 Calibration: Constrained Weight Optimization
- Maximize human correlation (Spearman ρ)
- 5-fold CV on calibration set (60%)
- Final weights evaluated on holdout (20%)

### 5.5 Threshold Calibration: Cost-Sensitive
- FP cost = 3× FN cost (user impact > retry cost)
- Youden Index + cost-sensitive optimization
- Holdout validation mandatory

### 5.6 Promotion Rule: ALL 10 Criteria Required
| # | Criterion |
|---|-----------|
| 1 | Valid Definition |
| 2 | Reliable Measurement |
| 3 | Human Evaluation Evidence (κw ≥0.60) |
| 4 | Reference Evidence (≥50 GOLD/SILVER) |
| 5 | Reproducible Methodology |
| 6 | Calibration Evidence (ρ ≥0.65 aggregate) |
| 7 | Holdout Validation (AUC ≥0.80) |
| 8 | Error Analysis (FP/FN categorized) |
| 9 | Stability (across strata) |
| 10 | Production Suitability (net value > cost) |

**Missing ANY → DO NOT PROMOTE**

---

## 6. Validation Results

### Static Validation

| Check | Result |
|-------|--------|
| `python -m compileall artifacts/ -q` | ✅ PASS (no artifacts are .py) |
| `git diff --check` | ✅ PASS (only CRLF warnings on pre-existing files) |

### Regression Tests (All PASS)

| Suite | Collected | Passed | Failed |
|-------|-----------|--------|--------|
| S6-02 TXT | 6 | 6 | 0 |
| S6-03 EPUB | 7 | 7 | 0 |
| S6-04 Validation | 16 | 16 | 0 |
| S6-05 Dry-Run | 8 | 8 | 0 |
| **Total** | **37** | **37** | **0** |

### Production Safety

| Metric | Value |
|--------|-------|
| Real Translation Execution | 0 |
| Provider Execution | 0 |
| Network Execution | 0 |
| Production Files Modified | 0 |
| Model Changed | NO |
| Provider Changed | NO |

---

## 7. Artifacts Produced

| Artifact | Path |
|----------|------|
| **Design Document** | `artifacts/NTPE_S7_09_LITERARY_QUALITY_EVALUATION_CALIBRATION_DESIGN.md` |
| **Design Report** | `artifacts/NTPE_S7_09_LITERARY_QUALITY_EVALUATION_CALIBRATION_DESIGN_REPORT.md` |

---

## 8. Working Tree Safety

| Check | Status |
|-------|--------|
| Pre-existing modifications preserved | ✅ 4 literary output files unchanged |
| Historical artifacts preserved | ✅ 25+ untracked artifacts untouched |
| No root scratch files created | ✅ |
| No unexpected root artifacts | ✅ |

---

## 9. Compliance Checklist (All 62 PASS Criteria)

| Category | Status |
|----------|--------|
| S7-07 contract consumed | ✅ |
| S7-08 evidence gaps consumed | ✅ |
| Evaluation objectives defined | ✅ |
| Corpus design defined | ✅ |
| Sampling methodology defined | ✅ |
| Evaluation unit defined | ✅ |
| Candidate provenance defined | ✅ |
| Reference translation policy defined | ✅ |
| Human rubric defined | ✅ |
| Human evaluator protocol defined | ✅ |
| Blind evaluation rules defined | ✅ |
| Pairwise evaluation method defined | ✅ |
| Inter-rater agreement methodology defined | ✅ |
| PS-03 calibration methodology defined | ✅ |
| Threshold calibration methodology defined | ✅ |
| Calibration/validation/holdout split defined | ✅ |
| Leakage prevention defined | ✅ |
| FP/FN methodology defined | ✅ |
| Best Attempt evidence protocol defined | ✅ |
| Segment Recovery evidence protocol defined | ✅ |
| Context Continuity evidence protocol defined | ✅ |
| Reviewer/Editor/ACE evidence protocol defined | ✅ |
| Dataset schema defined | ✅ |
| Reproducibility/versioning defined | ✅ |
| Pilot study defined | ✅ |
| Stopping criteria defined | ✅ |
| Promotion criteria defined | ✅ |
| No unsupported threshold introduced | ✅ |
| No production code changed | ✅ |
| No real translation | ✅ |
| No provider/network execution | ✅ |
| Retry boundary unchanged | ✅ |
| Model/provider unchanged | ✅ |
| Context feature remains off | ✅ |
| Existing contracts preserved | ✅ |
| Root hygiene preserved | ✅ |

---

## 10. Final Verdict

```
S7_09_LITERARY_QUALITY_EVALUATION_CALIBRATION_DESIGN_COMPLETE
```

### Summary

**Design Complete For**: All 10 non-production literary quality areas from S7-07/S7-08.

**Evidence Gaps Documented**: All promotion pathways explicitly blocked by missing evidence (no human evaluation dataset, no reference corpus, no calibration basis for PS-03 weights/thresholds).

**Framework Ready**: Complete, auditable framework from corpus construction through pilot study, calibration, holdout validation, to promotion decision.

**No Production Changes**: Zero modifications to production code, model, provider, retry boundary, or context feature.

**All Regression Tests Pass**: 37/37 S6 acceptance tests pass.

**Artifacts Produced**: Two formal documents in `artifacts/`.

---

*End of Report*

**Report Path**: `artifacts/NTPE_S7_09_LITERARY_QUALITY_EVALUATION_CALIBRATION_DESIGN_REPORT.md`
**Design Status**: `S7_09_DESIGN_COMPLETE`