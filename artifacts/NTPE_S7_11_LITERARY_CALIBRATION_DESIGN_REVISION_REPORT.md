# NTPE S7-11 — Literary Calibration Design Revision 01 Report

**Revision Date**: 2026-09-30
**Author**: Kilo (Automated)
**Scope**: Methodology revision of S7-09 v1.0 per S7-10 findings

---

## 1. Baseline

| Metric | Value |
|--------|-------|
| Baseline HEAD | `5b41e3d55b5d07f6e8d1fec2ea10fd83d22aedf5` ✓ |
| Actual HEAD | `5b41e3d55b5d07f6e8d1fec2ea10fd83d22aedf5` ✓ |
| Branch | `main` ✓ |
| Working Tree | 4 modified (pre-existing literary outputs), 25+ untracked (pre-existing artifacts) |
| Upstream | `origin/main` (`942650d...`) — not modified |

---

## 2. S7-10 Findings Consumed

**Input**: `artifacts/NTPE_S7_10_LITERARY_CALIBRATION_DESIGN_INTERNAL_AUDIT_REPORT.md`
**S7-10 Verdict**: `S7_10_CALIBRATION_DESIGN_REQUIRES_REVISION`
**Consumed**: YES

---

## 3. Revision Scope

S7-11 produces **Calibration Design v1.1** (new file; v1.0 preserved):

| Artifact | Path |
|----------|------|
| Revised Design | `artifacts/NTPE_S7_11_LITERARY_QUALITY_EVALUATION_CALIBRATION_DESIGN_V1_1.md` |
| This Report | `artifacts/NTPE_S7_11_LITERARY_CALIBRATION_DESIGN_REVISION_REPORT.md` |

No changelog artifact created (not needed; revisions are fully documented here and in v1.1).

---

## 4. H01 Sample Size Revision

| Aspect | S7-09 v1.0 | S7-11 v1.1 |
|--------|------------|------------|
| 50 passages | Ambiguous pilot/calibration role | **PILOT_ONLY** (explicit) |
| Formal sample size | 500-1000 raw target | **TBD — power analysis on n_eff** |
| Power analysis | Absent | Added: effect size, α, β, ICC, DE, attrition |

**Result**: RESOLVED

---

## 5. H02 Clustering Revision

| Aspect | v1.0 | v1.1 |
|--------|------|------|
| Independence | Treated passages as independent | Formal hierarchy: author→chapter→scene→passage |
| Design effect | Absent | `DE = 1 + (m̄−1)·ICC` added |
| Effective N | Not used | `n_eff = N_raw / DE` is primary quantity |
| Split unit | Chapter | Chapter-grouped + author-aware |

**Result**: RESOLVED

---

## 6. H03 Rubric Revision

| Aspect | v1.0 | v1.1 |
|--------|------|------|
| Overlap | Unacknowledged | Explicit overlap table (4 pairs) |
| Method | "PCA will prove independence" implied | **Ordinal EFA (polychoric)**; PCA diagnostic only |
| Factor count | Unspecified | No forced count; parallel analysis |
| Double-counting | Unaddressed | Covariance reporting; flag \|ρ\|>0.70; latent-factor option |

**Result**: RESOLVED

---

## 7. H04 Ordinal Analysis Revision

| Aspect | v1.0 | v1.1 |
|--------|------|------|
| Scale | Mixed ordinal/continuous | **Likert = ordinal** |
| Pearson r | Primary | Demoted to exploratory, `ASSUMPTION-DEPENDENT` |
| ICC(2,1) | Used standard | ICC(2,k) agreement + ordinal ICC; standard tagged assumption-dependent |
| Continuous methods | Untagged | All tagged + sensitivity analysis |

**Result**: RESOLVED

---

## 8. H05 Agreement Metric Revision

| Metric | v1.0 | v1.1 |
|--------|------|------|
| Weighted κw | Weighting unspecified | **Quadratic** (linear sensitivity); bootstrap CI |
| ICC | "ICC(2,1)" only | Family/type/measure/ordinal/missing/CI specified |
| Bradley-Terry | Unspecified | Graph/tie/intransitivity/balance/sparse/CI specified |
| Below-target | Silent | Escalation ladder (rubric→training→overlap→distribution→prevalence) |

**Result**: RESOLVED

---

## 9. H06 Numerical Target Revision

| Target | v1.0 | v1.1 |
|--------|------|------|
| 50 passages | Implied sample size | PILOT_ONLY |
| 3–5 evaluators | Requirement | PRE-REGISTERED PILOT TARGET |
| κw ≥0.60 | Design target | PRE-REGISTERED TARGET |
| ρ ≥0.70 | Design target | PRE-REGISTERED TARGET |
| Context ≥65% | Design target | PRE-REGISTERED TARGET |
| Reviewer/Editor/ACE ≥60% | Design target | PRE-REGISTERED TARGET |
| FP:FN 3:1 | Stated fact | UNSUPPORTED ASSUMPTION |
| 60/20/20 | Design target | PRE-REGISTERED TARGET |

A **Numerical Target Registry** (§26 of v1.1) classifies every value. **No value is VALIDATED.**

**Result**: RESOLVED

---

## 10. H07 Weight Optimization Revision

| Aspect | v1.0 | v1.1 |
|--------|------|------|
| n_eff/params | Unspecified | **≥10 required** |
| CV | 5-fold flat | **Nested CV** (inner tune, outer estimate) |
| Stability | Unspecified | Per-fold reporting; UNSTABLE flag |
| Constraints | Sum + bounds | Marked **TBD — pre-calibration** |
| Isotonic | Plain | Penalized (CV penalty) |
| Leakage | Chapter-grouped CV needed | Explicit grouped CV |

**Result**: RESOLVED

---

## 11. H08 Reference Contamination Revision

| Aspect | v1.0 | v1.1 |
|--------|------|------|
| Creator/evaluator | Not separated | **Hard rule**: reference creator ≠ primary evaluator |
| Role table | Absent | Creator / Reviewer / Generator / Evaluator roles |
| Provenance matrix | Partial | Full GOLD/SILVER/BRONZE × creator/review/uses/splits |
| Metric leakage | Absent | `selection_independent_of_ps03` guard |

**Result**: RESOLVED

---

## 12. Secondary Revisions

| Area | v1.1 Change |
|------|-------------|
| Split strategy | Chapter-grouped + author-aware; grouped CV |
| Leakage controls | Deduplication matrix; semantic dedup; evaluator pool separation |
| Pairwise protocols | Symmetric vs asymmetric separated; confound control; detectability check |
| Reference matrix | SILVER/BRONZE splits defined |
| Fatigue | Operational fields; TBD from pilot (not arbitrary) |
| Missing data | missing/abstain/invalid/inattentive/excluded with predefined rules |
| Outlier policy | Pre-registered, outcome-blind, sensitivity analysis |
| Pre-registration | Required field list |
| Confirmatory/exploratory | Explicit separation |
| Multiple testing | Primary pre-registered; no target shopping |
| Stopping rules | Result-dependent stopping prohibited |
| Cost/value | Framework; no invented monetary values |
| Binary label conflict | Resolution rule added |

---

## 13. Revised Methodology — Summary

See v1.1 §4–§31 for full detail. The v1.1 adds:
- Formal cluster/design-effect framework
- Formal sample size framework (TBD pending power analysis)
- Ordinal EFA policy
- Full agreement-metric specifications
- Nested CV + stability for weight optimization
- Role separation for reference/evaluator
- Pre-registration requirements
- Numerical Target Registry
- Statistical Method Matrix
- Sample Size Matrix
- Bias/Leakage Matrix

---

## 14. Numerical Target Registry

See v1.1 §26. Summary:

| Metric / Rule | Value | Status |
|---------------|------:|--------|
| Pilot passages | 50 | PILOT_ONLY |
| Evaluators | 3–5 | PRE-REGISTERED PILOT TARGET |
| κw | ≥0.60 | PRE-REGISTERED TARGET |
| Best Attempt ρ | ≥0.70 | PRE-REGISTERED TARGET |
| Context win | ≥65% | PRE-REGISTERED TARGET |
| Reviewer/Editor/ACE | ≥60% | PRE-REGISTERED TARGET |
| FP:FN | 3:1 | UNSUPPORTED ASSUMPTION |
| Split | 60/20/20 | PRE-REGISTERED TARGET |
| Spearman ρ dim/agg | ≥0.50 / ≥0.65 | PRE-REGISTERED TARGET |
| AUC / ECE | ≥0.80 / ≤0.05 | PRE-REGISTERED TARGET |

---

## 15. Leakage / Bias Controls

See v1.1 §16 and §29 (Bias/Leakage Matrix). Includes chapter leakage, near-duplicate, reference contamination (CRITICAL), position bias, learning effect, metric leakage (CRITICAL), overfitting, target shopping.

---

## 16. Pilot / Calibration Boundary

v1.1 §30–§31:
- Pilot = feasibility only (50 = PILOT_ONLY)
- Calibration = separate future task requiring power analysis + pre-registration
- Re-audit (S7-12) required before calibration execution

---

## 17. Remaining Methodology Risks

| Risk | Status |
|------|--------|
| ICC/DE unknown until pilot | TBD — expected; not a defect |
| Sample size unknown until pilot | TBD — expected; framework defined |
| Weight constraints unspecified | TBD — pre-calibration choice |
| Evaluator count (3–5) unvalidated | PRE-REGISTERED PILOT TARGET |
| All numerical targets unvalidated | Correctly classified; none promoted |
| 80/65 remain uncalibrated | FROZEN; evaluation method defined only |

**No HIGH-level methodology defect remains open.** Remaining items are legitimately deferred to pilot/empirical evidence.

---

## 18. Calibration Readiness

```
READY_FOR_REAUDIT
```

**Rationale**: All S7-10 HIGH findings addressed; no unresolved critical methodology defect; numerical targets properly classified; production boundary preserved; design internally coherent.

**Explicitly NOT** `READY_FOR_CALIBRATION`. Recommended progression: `S7-11 → READY_FOR_REAUDIT → S7-12 Re-Audit → CALIBRATION AUTHORIZED`.

---

## 19. Production Boundary Verification

| Boundary | Status |
|----------|--------|
| Model | `meta/llama-3.2-90b-vision-instruct` (unchanged) |
| Provider | `nvidia` (unchanged) |
| Retry boundary | PRESERVED |
| Context | `quality_context_scene_v72=false` |
| PS-03 weights | 30/20/20/15/10/5 (unchanged) |
| Thresholds | 80/65 (unchanged) |
| Production code modified | NO |

---

## 20. Regression Tests

| Suite | Collected | Passed | Failed |
|-------|-----------|--------|--------|
| S6-02 TXT | 6 | 6 | 0 |
| S6-03 EPUB | 7 | 7 | 0 |
| S6-04 Validation | 16 | 16 | 0 |
| S6-05 Dry-Run | 8 | 8 | 0 |
| **Total** | **37** | **37** | **0** |

Baseline preserved (37/37 → 37/37).

---

## 21. Real Translation Execution

```
0
```

## 22. Provider / Network Execution

```
0
```

## 23. Production Files Modified

```
NO
```

## 24. Root Hygiene

```
PASS
```

No root scratch files; artifacts under `artifacts/`; pre-existing changes preserved.

---

## 25. Final Verdict

```
S7_11_CALIBRATION_DESIGN_REVISION_01_COMPLETE_READY_FOR_REAUDIT
```

### Summary

- All 8 HIGH findings (H01–H08) resolved in v1.1
- All secondary MEDIUM/LOW findings addressed
- Numerical Target Registry complete; no target promoted to VALIDATED
- Production boundary fully preserved
- 37/37 regression tests pass
- 0 real translation, 0 provider/network execution
- No commit/push/tag

**Next step**: `S7-12 Calibration Design Re-Audit` (separate task).

---

*End of Report*

**Report Path**: `artifacts/NTPE_S7_11_LITERARY_CALIBRATION_DESIGN_REVISION_REPORT.md`
**Status**: `READY_FOR_REAUDIT`