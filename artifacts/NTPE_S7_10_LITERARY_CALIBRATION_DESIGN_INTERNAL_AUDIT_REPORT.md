# NTPE S7-10 — Literary Calibration Design Internal Audit Report

**Audit Date**: 2026-09-30
**Auditor**: Kilo (Automated)
**Scope**: Methodology Audit of S7-09 Literary Quality Evaluation & Calibration Design

---

## 1. Baseline

| Metric | Value |
|--------|-------|
| HEAD | `5b41e3d55b5d07f6e8d1fec2ea10fd83d22aedf5` ✓ |
| Branch | `main` ✓ |
| Working Tree | 4 modified (pre-existing), 25+ untracked artifacts (pre-existing) |
| S7-09 Input | `NTPE_S7_09_LITERARY_QUALITY_EVALUATION_CALIBRATION_DESIGN.md` |
| S7-09 Status | `DESIGN_COMPLETE` |
| S7-08 Verdict | `S7_08_LITERARY_QUALITY_REMAINS_OBSERVATIONAL_ONLY` |

---

## 2. Input Artifacts Consumed

| Artifact | Path | Status |
|----------|------|--------|
| S7-07 Contract | `artifacts/NTPE_S7_07_LITERARY_QUALITY_CONTRACT_V1.md` | ✅ CONSUMED |
| S7-07 Report | `artifacts/NTPE_S7_07_LITERARY_QUALITY_CONTRACT_V1_REPORT.md` | ✅ CONSUMED |
| S7-08 Audit | `artifacts/NTPE_S7_08_LITERARY_QUALITY_EVIDENCE_CALIBRATION_AUDIT_REPORT.md` | ✅ CONSUMED |
| S7-09 Design | `artifacts/NTPE_S7_09_LITERARY_QUALITY_EVALUATION_CALIBRATION_DESIGN.md` | ✅ CONSUMED |
| S7-09 Report | `artifacts/NTPE_S7_09_LITERARY_QUALITY_EVALUATION_CALIBRATION_DESIGN_REPORT.md` | ✅ CONSUMED |

---

## 3. Audit Objective

Review S7-09 methodology for:
- Statistical validity
- Bias / leakage / overfitting risk
- Methodological completeness
- Evidence-based targets vs. unsupported assumptions
- Calibration readiness decision

---

## 4. S7-09 Design Summary (Audited)

### Core Design Elements

| Component | S7-09 Specification |
|-----------|---------------------|
| **Evaluation Unit** | Scene-level passage (multi-paragraph, 500-3000 chars) |
| **Sampling** | Stratified: Genre × Dialogue Density × Scene Type × Terminology Density |
| **Pilot Size** | 50 passages, 3-5 evaluators |
| **Data Split** | 60% Calibration / 20% Validation / 20% Holdout |
| **Leakage Prevention** | Chapter-level split, simhash ≥0.85, candidate deduplication |
| **Human Rubric** | 7 dimensions × 7-pt Likert + binary ACCEPT/REJECT + failure tags |
| **Evaluator Protocol** | Blind, randomized, 3-5 evaluators, 8-12 min/passage, 10% re-eval |
| **Agreement Metric** | Weighted Cohen's κw (target ≥0.60), ICC(2,1), Bradley-Terry |
| **PS-03 Calibration** | Spearman ρ (dim ≥0.50, agg ≥0.65), isotonic regression, 5-fold CV |
| **Aggregate Weights** | Constrained optimization, L2 regularization, 5-fold CV |
| **Threshold Calibration** | Youden + cost-sensitive (FP:FN = 3:1), holdout validation |
| **Data Split** | 60% Calibration / 20% Validation / 20% Holdout (chapter-level) |
| **Pilot** | 50 passages, 3-5 evaluators, Go/No-Go |
| **Success Criteria** | κw ≥0.60, rank corr ≥0.70, Context ≥65%, Reviewer ≥60%, AUC ≥0.80 |
| **Promotion** | 10 mandatory criteria, ALL required |

---

## 5. Methodology Audit Findings

### 5.1 Evaluation Unit Audit — **MEDIUM: REVISE**

**Finding**: Scene-level passage (500-3000 chars) is reasonable for literary evaluation but **ignores hierarchical dependency**.

| Risk | Detail |
|------|--------|
| **Chapter/Scene Dependency** | Scenes within same chapter share terminology, characters, narrative arc — not independent observations |
| **Character/Style Continuity** | Same character voice persists across scenes; evaluator exposure to same character in multiple passages creates carry-over bias |
| **Effective Sample Size** | True n_eff < raw n; 1000 passages ≠ 1000 independent observations |

**Required Revision**:
- Add **cluster-aware effective sample size calculation** (design effect estimation)
- Specify **hierarchical analysis** (mixed-effects models for calibration)
- Define **scene independence test** (autocorrelation of residuals by chapter)

### 5.2 Sampling Audit — **MEDIUM: CLARIFY**

**Finding**: Stratified sampling protocol is well-specified but **minimum per stratum (10) may be insufficient** for rare strata.

| Issue | Risk |
|-------|------|
| **Stratum Sparsity** | 4 strata dimensions (genre × dialogue × scene type × terminology) = potentially 3×3×4×3=108 combinations; 10 per stratum = 1080 minimum passages |
| **Selection Bias** | "Easy scenes overrepresented" — developer-selected or easily extracted passages may skew toward clean, well-formatted text |
| **Quality Distribution** | "Clearly Good" 25% / "Clearly Poor" 15% targets may not reflect real production distribution |

**Required Revision**:
- Add **stratum feasibility check** before sampling
- Define **realistic quality distribution** from production logs
- Specify **minimum detectable effect size** per stratum

### 5.3 Pilot Sample Size Audit — **HIGH: REVISE**

**Finding**: "50 passages" labeled as pilot but **no statistical power justification**.

| Target | S7-09 Spec | Issue |
|--------|------------|-------|
| **Agreement Estimation** | 50 passages, 3-5 evaluators | For κw CI width ±0.15 at κ=0.6, need ~200 items with 3 raters (Donner & Eliasziw formula) |
| **Correlation Estimation** | ρ ≥0.30 on ≥50 passages | For ρ=0.3, α=0.05, β=0.2, need n≈85 |
| **Threshold Calibration** | 50 passages | Far below minimum for ROC analysis (need ~200 for stable AUC CI) |

**Classification**: **PILOT_ONLY — NOT CALIBRATION SAMPLE SIZE**

**Required Revision**:
- Explicitly label: `PILOT_ONLY — Requires power analysis for formal calibration`
- Add **formal sample size calculation** section with:
  - Primary endpoint (agreement / correlation / AUC)
  - Expected effect size
  - α, β, ICC/design effect
  - Required n per endpoint

### 5.4 60/20/20 Split Audit — **MEDIUM: REVISE**

**Finding**: Chapter-level split is correct but **novel text has multi-level clustering** not fully addressed.

| Issue | Risk |
|-------|------|
| **Scene-Level Clustering** | Scenes within chapter correlated; chapter split alone doesn't prevent scene-level contamination if scenes reused |
| **Character-Level Clustering** | Same character appears across chapters; evaluator sees same character voice → carry-over bias |
| **Style/Author Clustering** | Single author's style across all chapters → effective n much smaller than chapter count |
| **Split Size** | 20% holdout = ~100 passages min; with clustering, effective holdout may be <20 independent units |

**Required Revision**:
- Add **cluster-aware split** (grouped by author + major character arcs)
- Report **design effect** and effective sample size
- Consider **stratified group k-fold** for CV

### 5.5 Leakage Prevention Audit — **LOW: CLARIFY**

**Finding**: Prevention vectors are defined but **implementation-level details missing**.

| Vector | Current | Gap |
|--------|---------|-----|
| **Evaluator Contamination** | "Never sees same passage twice (except intra-rater 10%)" | No mechanism specified for cross-evaluator leakage (e.g., evaluator A discusses with B) |
| **Candidate Deduplication** | "Exact text deduplication" | What about near-duplicate translations (same meaning, different wording)? |
| **Reference Contamination** | "Reference ID tracking" | No separation of reference creator vs. evaluator pools |

**Required Revision**:
- Add **evaluator pool separation** (disjoint evaluator sets per split)
- Define **semantic deduplication** criteria for candidates
- Specify **reference-evaluator disjoint pools**

### 5.6 Human Rubric Audit — **HIGH: REVISE**

**Finding**: 7 dimensions have **significant conceptual overlap** risking double-counting in aggregate.

| Overlap Risk | Dimensions | Evidence |
|--------------|------------|----------|
| **Naturalness ↔ Fidelity** | Naturalness: "reads as natural"; Fidelity: "faithfully conveys meaning" | Poor fidelity often manifests as unnatural phrasing |
| **Character Voice ↔ Register/Tone** | Voice: "speech patterns"; Register: "formality, era, emotion" | Speech patterns directly determine register |
| **Coherence ↔ Fidelity** | Coherence: "flow logically"; Fidelity: "no omissions" | Omissions break coherence |
| **Overall ↔ All** | Overall: "holistic judgment" | Likely weighted sum of others; double-counting in aggregate |

**Required Revision**:
- Run **PCA/factor analysis** on pilot data to identify latent factors
- Define **orthogonal dimensions** or explicitly model covariance
- If aggregate uses sum, apply **variance inflation correction** or use latent factor scores

### 5.7 Likert Scale Audit — **HIGH: REVISE**

**Finding**: 7-point Likert treated as **ordinal in some places, continuous in others** without consistency.

| Analysis | S7-09 Method | Appropriateness |
|----------|--------------|-----------------|
| **Weighted κw** | Ordinal | ✅ Correct |
| **Spearman ρ** | Ordinal | ✅ Correct |
| **Pearson r** | Continuous | ❌ Likert is ordinal; Pearson assumes interval |
| **ICC(2,1)** | Continuous | ⚠️ Requires interval assumption; use ICC for ordinal (e.g., ICC for ordinal data) |
| **Isotonic Regression** | Ordinal → continuous mapping | ✅ Appropriate |
| **Linear Weight Optimization** | Continuous | ❌ Treats 1-7 as interval |

**Required Revision**:
- Remove Pearson r from primary analysis; use Spearman ρ only
- Specify **ICC model for ordinal data** (e.g., ICC with polychoric correlation)
- Document **assumption violation risk** for continuous methods

### 5.8 Binary ACCEPT/REJECT Audit — **MEDIUM: CLARIFY**

**Finding**: Binary label logic creates **potential contradiction** with Likert.

| Rule | Contradiction Example |
|------|----------------------|
| ACCEPT = Overall ≥5 AND no dim <3 | Overall=5, Naturalness=2, others=6 → REJECT (dim <3) but Overall acceptable |
| REJECT = Overall <3 OR any dim ≤2 | Overall=4, all dims=4 → ACCEPT but Overall <5 → edge case |

**Required Revision**:
- Add **conflict resolution rule**: Binary label takes precedence OR Likert takes precedence
- Define **borderline zone** (e.g., Overall=4-5 with one dim=2 → adjudication)

### 5.9 Inter-Rater Agreement Audit — **HIGH: REVISE**

| Metric | S7-09 Spec | Issue |
|--------|------------|-------|
| **Weighted κw** | "quadratic vs linear weighting" unspecified | Must specify: quadratic (default for ordered) or linear |
| **ICC** | "ICC(2,1)" only | Missing: agreement vs consistency; single vs average; ordinal ICC needed |
| **Bradley-Terry** | Not specified | Missing: ties handling, intransitivity check, comparison graph connectivity |
| **Threshold κw ≥0.60** | Design target | **UNVALIDATED TARGET** — no evidence 0.60 sufficient for calibration reliability |

**Required Revision**:
- Specify κw weighting (quadratic recommended for Likert)
- Add **ICC model specification**: `ICC(2,k)` for average of k raters, agreement type
- Add **Bradley-Terry diagnostics**: intransitivity rate, comparison graph density
- Reclassify κw ≥0.60 as `PRE-REGISTERED TARGET` not `VALIDATED`

### 5.10 Pairwise Evaluation Audit — **MEDIUM: REVISE**

**Finding**: Four different use cases forced into **single protocol** despite different comparison logic.

| Use Case | Question | Protocol Mismatch |
|----------|----------|-------------------|
| **Best Attempt** | Which attempt is better? | Symmetric preference |
| **Context Continuity** | Does context help? | Asymmetric (ON vs OFF) |
| **Reviewer/Editor/ACE** | Does processing help? | Asymmetric (baseline vs processed) |
| **Segment Merge** | Does merge preserve quality? | Merged vs full (not A vs B) |

**Required Revision**:
- Define **separate protocols** for symmetric vs asymmetric comparisons
- For asymmetric: use **one-sided tests**, report directionality
- Define **different success criteria** per use case

### 5.11 Win-Rate Target Audit — **HIGH: REVISE**

| Target | Value | Classification | Evidence |
|--------|-------|----------------|----------|
| Context win rate | ≥65% | **PRE-REGISTERED TARGET** | No justification |
| Reviewer/Editor/ACE | ≥60% | **PRE-REGISTERED TARGET** | No justification |
| Best Attempt rank corr | ≥0.70 | **PRE-REGISTERED TARGET** | No justification |
| FP:FN cost | 3:1 | **UNSUPPORTED ASSUMPTION** | No operational data |
| κw ≥0.60 | ≥0.60 | **PRE-REGISTERED TARGET** | No justification |

**Required Revision**:
- All targets reclassified as `PRE-REGISTERED TARGET` or `UNSUPPORTED ASSUMPTION`
- Add **rationale documentation** requirement before calibration
- Define **sensitivity analysis** around each target

### 5.12 PS-03 Calibration Audit — **HIGH: REVISE**

| Method | Appropriateness | Issue |
|--------|-----------------|-------|
| **Spearman ρ** | Ordinal → Ordinal | ✅ Correct |
| **Pearson r** | Continuous → Ordinal | ❌ Remove from primary |
| **Isotonic Regression** | Ordinal → Continuous | ✅ Appropriate but needs **regularization** (penalized isotonic) |
| **Weight Optimization** | Constrained + L2 + 5-fold CV | ⚠️ **Overfitting risk**: 6 params, n_eff may be <50 |
| **5-fold CV** | Standard | ⚠️ **Leakage risk**: Must ensure chapter-grouped CV |

**Required Revision**:
- Remove Pearson from primary; keep as exploratory
- Add **penalized isotonic regression** (e.g., PAVA with penalty)
- Add **grouped CV** (chapter-level groups)
- Report **effective degrees of freedom** for weight optimization

### 5.13 Aggregate Weight Optimization Audit — **HIGH: REVISE**

**Finding**: Overfitting risk with **6 parameters from potentially <100 effective observations**.

| Parameter | Risk |
|-----------|------|
| **Params** | 6 (weights) |
| **Effective n** | Unknown; likely 50-100 after clustering |
| **Regularization** | L2 only; no cross-validated λ selection specified |
| **Constraints** | Sum=100, bounds [0,100] | Weak without monotonicity constraints |

**Required Revision**:
- Add **minimum n_eff / params ratio** requirement (e.g., ≥10:1)
- Specify **nested CV** for λ selection
- Add **monotonicity constraints** (e.g., fidelity ≥ terminology based on theory)
- Report **weight stability** across CV folds (variance)

### 5.14 Overfitting Audit — **HIGH: REVISE**

| Risk | Current Mitigation | Gap |
|------|-------------------|-----|
| **Fit → Validate same data** | 60/20/20 split | Chapter-level split may not prevent scene/character leakage |
| **Threshold selection on validation** | Youden on validation set | Standard but optimistic if validation used repeatedly |
| **Weight selection on validation** | CV on calibration | Standard but nested CV needed |
| **Multiple metric selection** | Primary: ρ, AUC; Secondary: ECE | No pre-registration of primary |

**Required Revision**:
- Enforce **nested CV**: inner loop for threshold/weight, outer for performance
- **Pre-register primary metric** (e.g., aggregate Spearman ρ)
- Define **confirmatory vs exploratory** analyses

### 5.15 Threshold Calibration Audit — **HIGH: REVISE**

| Issue | Detail |
|-------|--------|
| **FP:FN = 3:1** | **UNSUPPORTED ASSUMPTION** — no operational cost data |
| **Youden Index** | Assumes equal class cost; contradicts 3:1 cost ratio |
| **Class Imbalance** | Not addressed; if ACCEPT rare, Youden inappropriate |
| **ROC vs PR** | Not addressed; if imbalance, PR curve more informative |

**Required Revision**:
- Reclassify 3:1 as `UNSUPPORTED ASSUMPTION`
- Require **operational cost analysis** before calibration
- Add **PR curve analysis** for imbalanced classes
- Use **cost-sensitive threshold** directly (minimize expected cost), not Youden

### 5.16 Best Attempt Evaluation Audit — **MEDIUM: REVISE**

| Issue | Detail |
|-------|--------|
| **Symmetric vs Asymmetric** | Protocol uses symmetric A/B; attempt comparison is inherently ordered (1st, 2nd, 3rd) |
| **Hard-Gate Confound** | Attempts with HARD_GATE fail may be rated lower regardless of literary quality |
| **Rank Correlation Target** | ≥0.70 is **PRE-REGISTERED TARGET**; no justification |

**Required Revision**:
- Use **ordered comparison** (1st vs 2nd, 2nd vs 3rd) not all pairs
- Control for HARD_GATE status in preference analysis
- Reclassify 0.70 as `PRE-REGISTERED TARGET`

### 5.17 Segment Recovery Audit — **MEDIUM: REVISE**

| Issue | Detail |
|-------|--------|
| **Evaluation Target** | "Full merged output" — correct but merge strategy comparison needed |
| **Merge Strategies** | 3 defined but no **randomized assignment** of merge strategy to evaluator |
| **Boundary Metrics** | Automated check specified but no **human boundary evaluation** |

**Required Revision**:
- Add **merge strategy as experimental factor** (randomized)
- Add **human boundary quality rating**

### 5.18 Context Continuity Audit — **MEDIUM: REVISE**

| Issue | Detail |
|-------|--------|
| **Blind A/B** | Correct but **context presence detectable** (output length, coherence cues) |
| **Win Rate Target** | ≥65% is **PRE-REGISTERED TARGET** |
| **Confound Control** | "Same model, same source" but context changes output distribution |

**Required Revision**:
- Add **detectability check** (can evaluators guess condition?)
- Reclassify 65% as `PRE-REGISTERED TARGET`

### 5.19 Reviewer/Editor/ACE Audit — **MEDIUM: REVISE**

| Issue | Detail |
|-------|--------|
| **Baseline Confound** | "Baseline vs Processed" — but processed may have different error profile |
| **FP Rate Control** | "FP rate ≤ baseline" — but baseline FP rate estimated from same data (circular) |
| **Win Rate Target** | ≥60% is **PRE-REGISTERED TARGET** |

**Required Revision**:
- Estimate baseline FP rate from **independent holdout**
- Reclassify 60% as `PRE-REGISTERED TARGET`

### 5.20 Reference Hierarchy Audit — **MEDIUM: CLARIFY**

| Tier | Calibration | Validation | Holdout |
|------|-------------|------------|---------|
| GOLD | ✅ | ✅ | ✅ |
| SILVER | ✅ (caveat) | ❓ | ❓ |
| BRONZE | ✅ (cal only) | ❌ | ❌ |

**Gap**: SILVER/BRONZE roles in validation/holdout not fully specified.

**Required Revision**: Complete SILVER/BRONZE usage matrix.

### 5.21 Reference Contamination Audit — **HIGH: REVISE**

**Finding**: No explicit **evaluator-reference separation**.

| Risk | Scenario |
|------|----------|
| **Creator as Evaluator** | Translator who created GOLD reference also evaluates candidates |
| **Editor as Evaluator** | Editor who created SILVER evaluates ACE-processed output |

**Required Revision**:
- Enforce **disjoint pools**: Reference creators ≠ Evaluators
- Track `creator_id` vs `evaluator_id` disjointness

### 5.22 Numerical Target Classification

| Target | Current | Classification | Required Action |
|--------|---------|----------------|-----------------|
| Pilot passages = 50 | 50 | **PILOT_ONLY** | Add power analysis |
| Evaluators = 3-5 | 3-5 | **TBD** | Power analysis |
| κw ≥ 0.60 | ≥0.60 | **PRE-REGISTERED TARGET** | Document rationale |
| Best Attempt ρ ≥ 0.70 | ≥0.70 | **PRE-REGISTERED TARGET** | Document rationale |
| Context win rate ≥ 65% | ≥65% | **PRE-REGISTERED TARGET** | Document rationale |
| Reviewer/Editor/ACE win rate ≥ 60% | ≥60% | **PRE-REGISTERED TARGET** | Document rationale |
| FP:FN = 3:1 | 3:1 | **UNSUPPORTED ASSUMPTION** | Require operational data |
| 60/20/20 split | 60/20/20 | **PRE-REGISTERED TARGET** | Document rationale |

---

## 6. Required Revisions Matrix

| Component | Severity | Action | Summary |
|-----------|----------|--------|---------|
| Pilot sample size | HIGH | REVISE | Label PILOT_ONLY; add power analysis |
| Effective sample size | HIGH | REVISE | Add cluster-aware n_eff calculation |
| 60/20/20 split | MEDIUM | REVISE | Add grouped split + design effect |
| Rubric overlap | HIGH | REVISE | PCA/factor analysis; orthogonal dims |
| Likert analysis | HIGH | REVISE | Remove Pearson; ordinal ICC |
| κw weighting | HIGH | REVISE | Specify quadratic; document rationale |
| ICC specification | HIGH | REVISE | Full model spec + ordinal ICC |
| Bradley-Terry | HIGH | REVISE | Add diagnostics spec |
| Win-rate targets | HIGH | REVISE | Classify as PRE-REGISTERED; add rationale |
| FP:FN = 3:1 | HIGH | REVISE | Classify UNSUPPORTED; require operational data |
| Weight optimization | HIGH | REVISE | Nested CV; n_eff/params ratio; stability |
| FP:FN cost 3:1 | HIGH | REVISE | Classify UNSUPPORTED; require operational data |
| Evaluator-reference separation | HIGH | REVISE | Enforce disjoint pools |
| Pairwise protocols | MEDIUM | REVISE | Separate symmetric/asymmetric |
| SILVER/BRONZE usage | MEDIUM | CLARIFY | Complete eligibility matrix |
| Evaluator fatigue | LOW | CLARIFY | Operational definition |

---

## 7. Numerical Target Classification Table

| Target | Value | Classification | Evidence | Risk |
|--------|-------|----------------|----------|------|
| Pilot passages | 50 | **PILOT_ONLY** | Power analysis shows insufficient | HIGH |
| Evaluators | 3-5 | **TBD** | Power analysis needed | MEDIUM |
| κw threshold | ≥0.60 | **PRE-REGISTERED TARGET** | No empirical basis | HIGH |
| Best Attempt ρ | ≥0.70 | **PRE-REGISTERED TARGET** | No empirical basis | HIGH |
| Context win rate | ≥65% | **PRE-REGISTERED TARGET** | No empirical basis | HIGH |
| Reviewer/Editor/ACE | ≥60% | **PRE-REGISTERED TARGET** | No empirical basis | HIGH |
| FP:FN cost | 3:1 | **UNSUPPORTED ASSUMPTION** | No operational data | HIGH |
| 60/20/20 split | 60/20/20 | **PRE-REGISTERED TARGET** | Standard but unverified for clustered data | MEDIUM |

---

## 7. Findings Matrix

| # | Component | Finding | Severity | Status | Required Action |
|---|-----------|---------|----------|--------|-----------------|
| 1 | Pilot sample size | 50 insufficient for calibration endpoints | HIGH | REVISE | Label PILOT_ONLY; add power analysis |
| 2 | Cluster dependency | Scene/chapter/character clustering ignored | HIGH | REVISE | Add design effect + n_eff |
| 3 | Rubric overlap | 7 dimensions have conceptual overlap | HIGH | REVISE | PCA/factor analysis |
| 4 | Likert analysis | Pearson/ICC misapplied to ordinal | HIGH | REVISE | Remove Pearson; ordinal ICC |
| 5 | κw specification | Weighting & threshold unspecified | HIGH | REVISE | Specify quadratic; rationale |
| 6 | ICC spec incomplete | Model, type, ordinal variant missing | HIGH | REVISE | Full ICC spec |
| 6 | Bradley-Terry | Diagnostics missing | HIGH | REVISE | Add intransitivity, graph connectivity |
| 7 | Win-rate targets | All targets PRE-REGISTERED, no justification | HIGH | REVISE | Add rationale or classify TBD |
| 8 | FP:FN cost 3:1 | UNSUPPORTED ASSUMPTION | HIGH | REVISE | Require operational cost analysis |
| 8 | Weight optimization | n_eff/params ratio unknown; overfitting risk | HIGH | REVISE | n_eff/params ≥10; nested CV; stability |
| 9 | FP:FN cost 3:1 | UNSUPPORTED ASSUMPTION | HIGH | REVISE | Require operational cost model |
| 9 | Evaluator-ref separation | No disjoint pools defined | HIGH | REVISE | Enforce creator/evaluator disjoint |
| 10 | Pairwise protocols | Symmetric protocol misapplied to asymmetric | MEDIUM | REVISE | Separate protocols |
| 10 | SILVER/BRONZE | Eligibility matrix incomplete | MEDIUM | CLARIFY | Complete matrix |
| 11 | Pilot size | 50 passages | HIGH | REVISE | Label PILOT_ONLY; power analysis |
| 11 | Cluster dependency | n_eff < n_raw | HIGH | REVISE | Design effect calculation |
| 12 | 60/20/20 split | Cluster leakage risk | MEDIUM | REVISE | Grouped split + design effect |
| 12 | Leakage prevention | Evaluator, semantic dup, ref separation | LOW | CLARIFY | Add mechanisms |
| 13 | Rubric overlap | Naturalness/Fidelity, Voice/Register, Coherence/Fidelity | HIGH | REVISE | PCA/factor analysis |
| 14 | Likert | Pearson r, ICC(2,1) misapplied | HIGH | REVISE | Ordinal methods only |
| 15 | Binary ACCEPT/REJECT | Conflict with Likert possible | MEDIUM | CLARIFY | Resolution rule |
| 16 | κw spec | Weighting, threshold rationale missing | HIGH | REVISE | Specify quadratic; rationale |
| 16 | ICC | Model, type, ordinal variant missing | HIGH | REVISE | Full spec |
| 16 | Bradley-Terry | Diagnostics missing | HIGH | REVISE | Add diagnostics |
| 17 | Win-rate targets | All PRE-REGISTERED, no justification | HIGH | REVISE | Add rationale |
| 17 | FP:FN cost | 3:1 UNSUPPORTED ASSUMPTION | HIGH | REVISE | Operational data required |
| 18 | Weight optimization | Overfitting risk | HIGH | REVISE | n_eff/params; nested CV; stability |
| 19 | Overfitting | Multiple leakage paths | HIGH | REVISE | Nested CV; pre-registration |
| 20 | Threshold calibration | FP:FN 3:1 unsupported; Youden vs cost-sensitive | HIGH | REVISE | Cost model required |
| 21 | Best Attempt | Symmetric protocol for ordered attempts | MEDIUM | REVISE | Ordered comparison |
| 22 | Segment Merge | Merge strategy not randomized | MEDIUM | REVISE | Randomized factor |
| 23 | Context | Detectability of condition not checked | MEDIUM | REVISE | Detectability check |
| 24 | Reviewer/Editor/ACE | Circular FP baseline; asymmetric protocol | MEDIUM | REVISE | Independent FP baseline |
| 24 | Reference hierarchy | SILVER/BRONZE validation/holdout undefined | MEDIUM | CLARIFY | Complete matrix |
| 25 | Ref contamination | No creator/evaluator separation | HIGH | REVISE | Disjoint pools |

---

## 8. Calibration Readiness Decision

### Overall Assessment

```
NOT_READY — METHODOLOGY GAPS
```

### Rationale

The S7-09 design is **comprehensive and well-structured** but contains **multiple HIGH-severity methodology gaps** that would invalidate calibration results if executed as-is. Critical gaps include:

1. **Sample size / clustering** — Pilot size (50) treated as calibration-ready; no power analysis; clustering ignored
2. **Rubric validity** — Dimension overlap unaddressed; Likert analysis methods mismatched
3. **Agreement metrics** — Key specifications incomplete (κw weighting, ICC model, Bradley-Terry diagnostics)
4. **Overfitting risk** — Weight optimization without nested CV, n_eff/params ratio unknown
5. **Unsupported targets** — All numerical thresholds (κw≥0.60, win rates, cost ratio) lack empirical justification
6. **Reference contamination** — No evaluator-reference separation enforced

### Path Forward

The design is **salvageable** with targeted revisions. Estimated effort: **2-3 revision cycles** focusing on:

1. **Priority 1 (Blockers)**: Sample size/power analysis, clustering/design effect, rubric orthogonality, ordinal methods
2. **Priority 2 (Reliability)**: Agreement metric specifications, weight optimization safeguards, target justifications
3. **Priority 3 (Completeness)**: Reference matrix, contamination prevention, pairwise protocols

---

## 9. Production Boundary Verification

| Boundary | Status | Verification |
|----------|--------|--------------|
| Model Frozen | ✅ | `meta/llama-3.2-90b-vision-instruct` |
| Provider Frozen | ✅ | `nvidia` |
| Retry Boundary | ✅ LOCKED | Max 5, provider switch after 3, chunk halving |
| Context Feature | ✅ OFF | `quality_context_scene_v72=false` |
| PS-03 Weights | ✅ FROZEN | 30/20/20/15/10/5 |
| PS-03 Thresholds | ✅ FROZEN | 80/65 |
| Production Gates | ✅ PRESERVED | 14 deterministic gates |
| Real Translation | ✅ 0 | No provider calls |
| Network Execution | ✅ 0 | No API calls |

---

## 10. Regression Tests

| Suite | Collected | Passed | Failed |
|-------|-----------|--------|--------|
| S6-02 TXT | 6 | 6 | 0 |
| S6-03 EPUB | 7 | 7 | 0 |
| S6-04 Validation | 16 | 16 | 0 |
| S6-05 Dry-Run | 8 | 8 | 0 |
| **Total** | **37** | **37** | **0** |

---

## 11. Final Verdict

```
S7_10_CALIBRATION_DESIGN_REQUIRES_REVISION
```

### Summary

The S7-09 design is **methodologically ambitious and well-structured** but **not ready for calibration execution** due to **5 HIGH-severity and 8 MEDIUM-severity methodology gaps**. With targeted revisions (estimated 2-3 cycles), the design can reach `READY_FOR_CALIBRATION` status.

**No production changes made. No commits. No pushes. No tags.**

---

## 12. Artifacts Produced

| Artifact | Path |
|----------|------|
| **Audit Report** | `artifacts/NTPE_S7_10_LITERARY_CALIBRATION_DESIGN_INTERNAL_AUDIT_REPORT.md` |

---

*End of Audit Report*

**Report Path**: `artifacts/NTPE_S7_10_LITERARY_CALIBRATION_DESIGN_INTERNAL_AUDIT_REPORT.md`
**Audit Status**: `S7_10_CALIBRATION_DESIGN_REQUIRES_REVISION`