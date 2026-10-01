# NTPE S7-11 — Literary Quality Evaluation & Calibration Design v1.1

**Revision**: 01 (v1.1)
**Supersedes**: `artifacts/NTPE_S7_09_LITERARY_QUALITY_EVALUATION_CALIBRATION_DESIGN.md` (v1.0, preserved)
**Revision Date**: 2026-09-30
**Author**: Kilo (Automated)
**Baseline HEAD**: `5b41e3d55b5d07f6e8d1fec2ea10fd83d22aedf5`
**Input**: S7-10 Internal Audit (`S7_10_CALIBRATION_DESIGN_REQUIRES_REVISION`)
**Status**: REVISION — No implementation, no calibration execution, no human study

---

## 0. Revision Scope

This v1.1 revises S7-09 v1.0 to address **all S7-10 HIGH and MEDIUM findings**:

| Finding | Severity | v1.1 Revision |
|---------|----------|---------------|
| H01 Pilot Size | HIGH | 50 = `PILOT_ONLY`; formal sample size framework added |
| H02 Clustering | HIGH | Design effect, effective sample size, hierarchical sampling |
| H03 Rubric Overlap | HIGH | Ordinal factor analysis policy; no forced PCA |
| H04 Ordinal Methods | HIGH | Likert = ordinal; Pearson/standard ICC demoted |
| H05 Agreement Specs | HIGH | Full κw / ICC / Bradley-Terry specifications |
| H06 Numerical Targets | HIGH | Target Registry with mandatory classification |
| H07 Weight Optimization | HIGH | n_eff/params ratio; nested CV; stability analysis |
| H08 Reference Contamination | HIGH | Role separation; provenance matrix |
| + Secondary | MEDIUM/LOW | Split, leakage, pairwise, fatigue, missing data, pre-registration |

---

## 1. Purpose

Define a **methodologically defensible** framework for acquiring, evaluating, and calibrating literary quality metrics. This framework must survive independent re-audit **before** any calibration execution.

**Core Principles (unchanged)**:
- No arbitrary thresholds promoted to production
- Every production gate traces to deterministic, evidence-backed measurement
- `Design assumption ≠ Pre-registered target ≠ Observed result ≠ Validated threshold ≠ Production contract`

---

## 2. Frozen Baseline & Boundaries

| Item | Value | Status |
|------|-------|--------|
| HEAD | `5b41e3d55b5d07f6e8d1fec2ea10fd83d22aedf5` | FROZEN |
| Branch | `main` | FROZEN |
| Model | `meta/llama-3.2-90b-vision-instruct` | FROZEN |
| Provider | `nvidia` | FROZEN |
| Retry boundary | max 5 attempts; provider switch after 3 (429/503/exhausted); chunk halving for empty/short/hangul/timeout; `provider_called=false` | FROZEN |
| Context feature | `quality_context_scene_v72=false` | FROZEN OFF |
| PS-03 weights | 30/20/20/15/10/5 | FROZEN |
| PS-03 thresholds | 80 / 65 | FROZEN (UNCALIBRATED) |
| Production gates | 14 deterministic gates (S7-07) | PRESERVED |

---

## 3. Current Quality Contract State

Unchanged from S7-09 v1.0 (see v1.0 §3). Deterministic production gates remain as defined in S7-07; non-production areas remain `OBSERVATIONAL_ONLY` / `NOT_IMPLEMENTED` / `FEATURE_GATED_OFF` per S7-08.

---

## 4. Evaluation Unit (Revised — H02)

### Primary Unit: Scene-Level Passage (multi-paragraph, 500-3000 chars)

### 4.1 Hierarchical Dependency Acknowledgment

The following hierarchy is **formally recognized**; passages are **NOT independent observations**:

```
author
  └── chapter
        └── scene
              └── passage
                    └── (character, terminology, style)
```

### 4.2 Cluster Variables

| Cluster Level | Variable | Impact |
|---------------|----------|--------|
| Author | `author_id` | Style, idiolect |
| Chapter | `chapter_id` | Narrative arc, terminology batch |
| Scene | `scene_id` | Local continuity, characters present |
| Character | `character_ids[]` | Voice, honorifics |
| Terminology batch | `terminology_group_id` | Locked term co-occurrence |

### 4.3 Design Effect & Effective Sample Size

```
n_eff = N_raw / DE
DE = 1 + (m̄ − 1) × ICC
```

| Term | Meaning | Status |
|------|---------|--------|
| `N_raw` | Raw passage count | Reported |
| `m̄` | Average cluster size | Reported |
| `ICC` | Intraclass correlation of the primary outcome | **TBD — estimated during pilot** |
| `DE` | Design effect | Computed from pilot |
| `n_eff` | Effective sample size | **Primary planning quantity** |

**Rule**: All sample-size planning uses `n_eff`, never `N_raw`.

### 4.4 Reported Quantities (mandatory)

Every calibration report must state: `raw N`, `cluster count` (author/chapter/scene), `average cluster size`, `ICC estimate`, `design effect`, `effective N`.

---

## 5. Corpus Design (Revised — H02)

### 5.1 Source Corpus Requirements

Unchanged from v1.0 §7.1 (language, genre, scene types, dialogue density, char count, sentence complexity, register, terminology density).

### 5.2 Corpus Size (Revised)

| Quantity | v1.0 | v1.1 |
|----------|------|------|
| Passages (raw) | 500-1000 | **TBD — Requires power analysis on effective N** |
| Chapters | ≥50 | TBD (cluster count) |
| Scenes | ≥200 | TBD |
| Authors | — | **≥3** (new: author-level cluster diversity) |

**Note**: Raw targets removed; replaced by `n_eff` planning (§7).

### 5.3 Stratum Feasibility Check (New — S7-10 §5.2)

Before sampling, verify each stratum is feasible:

| Check | Requirement |
|-------|-------------|
| Stratum population | ≥20 candidate passages available |
| Stratum retained | If <20, merge with adjacent stratum and document |
| Max strata | Cap at ≤24 strata to avoid sparsity |
| Selection-bias audit | Compare selected vs population on length/quality proxies |

### 5.4 Quality Distribution (Revised)

`Clearly Good 25% / Acceptable 35% / Borderline 25% / Clearly Poor 15%` is **reclassified as PRE-REGISTERED TARGET**, not a production prevalence claim. Future calibration must report both:
- Balanced analysis (as designed)
- Realistic-prevalence analysis (from production logs, when available)

---

## 6. Sampling Strategy (Revised — H02)

### 6.1 Cluster-Aware Sampling

1. **Strata**: genre × dialogue density × scene type × terminology density (capped ≤24)
2. **Sampling Unit**: complete scene (never split)
3. **Clustering**: sample whole chapters where possible; passages within a scene stay together
4. **Group Assignment**: all passages of a chapter/author assigned to the **same split**
5. **Author Balance**: authors distributed across splits by stratification if ≥3 authors
6. **Minimum per Stratum**: feasibility-driven (see §5.3)

### 6.2 Split Design (Revised — S7-10 §5.4)

| Set | v1.0 | v1.1 |
|-----|------|------|
| Calibration | 60% | 60% of **chapters** |
| Validation | 20% | 20% of **chapters** |
| Holdout | 20% | 20% of **chapters** |

**Split Unit = chapter** (grouped). Within-chapter scenes never cross splits.

**Grouped CV**: cross-validation folds must be grouped by chapter (and by author when ≥3 authors).

---

## 7. Formal Calibration Sample Size Framework (New — H01)

### 7.1 Pilot vs Calibration Separation

| Phase | Purpose | Sample | Status |
|-------|---------|--------|--------|
| **Pilot** | Feasibility, rubric clarity, agreement estimation, time burden | 50 passages | **PILOT_ONLY** |
| **Calibration** | Formal weight/threshold estimation | **TBD — power analysis** | NOT AUTHORIZED |

**50 passages is explicitly PILOT_ONLY.** It cannot support:
- Formal calibration validity
- Production threshold validation
- Stable AUC confidence intervals

### 7.2 Power Analysis Inputs (Required Before Calibration)

The future calibration task must specify:

| Input | Value | Status |
|-------|-------|--------|
| Primary endpoint | Aggregate Spearman ρ (or AUC) | PRE-REGISTERED |
| Expected effect size | TBD — from pilot | TBD |
| α | 0.05 | PRE-REGISTERED |
| Power (1−β) | 0.80 | PRE-REGISTERED |
| Expected ICC | TBD — from pilot | TBD |
| Average cluster size `m̄` | TBD — from pilot | TBD |
| Design effect `DE` | TBD | Derived |
| Attrition allowance | TBD | TBD |

### 7.3 Illustrative (Non-Binding) Calculations

| Endpoint | Assumption | Raw n | Cluster-adjusted |
|----------|------------|-------|------------------|
| Correlation ρ=0.30, α=.05, β=.20 | Independent observations | ≈85 | **n_eff ≈85** |
| Weighted κ CI width ±0.15 at κ=0.60, 3 raters | Independent items | ≈200 | **n_eff ≈200** |
| AUC CI width ±0.05 | Independent items | ≈200 | **n_eff ≈200** |

**These are illustrative only.** They assume independence and must be inflated by `DE` for clustered data. They do **not** constitute the final sample requirement.

---

## 8. Rubric Orthogonality (Revised — H03)

### 8.1 Dimension Overlap Risks (Acknowledged)

| Pair | Overlap Risk |
|------|--------------|
| Naturalness ↔ Fidelity | Poor fidelity can manifest as unnatural phrasing |
| Character Voice ↔ Register/Tone | Speech patterns determine register |
| Coherence ↔ Fidelity | Omissions break coherence |
| Overall ↔ all others | Potential double-counting |

### 8.2 Exploratory Factor Analysis Policy

- Purpose: study **construct redundancy, dimension separability, latent structure** — **not** to validate literary quality.
- Method choice based on ordinal data: **polychoric correlation + ordinal exploratory factor analysis (EFA)**; PCA permitted only as a supplementary diagnostic.
- **No forced factor count.** Retain factors by parallel analysis / scree with documented criteria.
- Pilot data only; **no production claim**; **no post-hoc factor manipulation to improve score**.

### 8.3 Dimension Reduction Rule

If evidence shows high overlap, the future design may recommend `MERGE`, `REDEFINE`, or `RETAIN WITH CAUTION`. This is a **future calibration design decision**; production PS-03 is **not modified** in this task.

### 8.4 Aggregate Double-Counting Guard

If the aggregate uses a simple sum, the future analysis must:
- Report dimension covariance
- Consider latent-factor or variance-inflation correction
- Flag any dimension pair with \|ρ\| > 0.70

---

## 9. Ordinal Data Policy (Revised — H04)

### 9.1 Scale Classification

**7-point Likert = ordinal response data.** It is **not** automatically interval.

### 9.2 Method-by-Purpose

| Purpose | Primary | Secondary / Sensitivity |
|---------|---------|-------------------------|
| Association | Spearman ρ / Kendall τ | (Pearson only as labelled exploratory) |
| Agreement | Weighted κ (ordinal) | ICC (ordinal-aware) |
| Reliability | Ordinal ICC / weighted κ | Krippendorff α |
| Pairwise | Bradley-Terry | Win-rate + bootstrap CI |

### 9.3 Continuous Approximation Policy

Any use of mean/SD/Pearson/linear ICC must be tagged **`ASSUMPTION-DEPENDENT`** and accompanied by a sensitivity analysis. Prohibited chain: `Likert → interval → Pearson → validated`.

---

## 10. Binary ACCEPT/REJECT (Revised — S7-10 §5.8)

### 10.1 Conflict Resolution Rule (New)

| Case | Resolution |
|------|------------|
| Binary and Likert agree | Use as-is |
| Binary ACCEPT but Overall ≤4 | **Binary takes precedence**; flag `LABEL_CONFLICT` |
| Binary REJECT but all dims ≥5 | **Binary takes precedence**; flag `LABEL_CONFLICT` |
| Borderline zone (Overall 4-5 OR exactly one dim=2) | **Adjudication required** |

### 10.2 Precedence Policy

The binary ACCEPT/REJECT label is the **primary classification outcome** for threshold calibration; Likert dimensions are the **measurement/association** outcome. Conflicts are reported, not silently averaged.

---

## 11. Agreement Metrics (Revised — H05)

### 11.1 Weighted Kappa — Full Specification

| Item | Specification |
|------|---------------|
| Weighting | **Quadratic** (default for ordered categories); linear reported as sensitivity |
| Categories | 7 ordinal |
| Missing labels | Excluded per §17 policy; reported |
| Confidence interval | Bootstrap (≥2000 resamples) |
| Minimum reporting | κw, CI, weighting, n, missing count |

`κw ≥ 0.60` = **PRE-REGISTERED TARGET** (not validated).

### 11.2 ICC — Full Specification

| Item | Specification |
|------|---------------|
| Family | ICC(2,k) primary (two-way random, average measure) for rater panels |
| Type | **Agreement** primary; consistency reported as sensitivity |
| Ordinal handling | Polychoric-based ordinal ICC preferred; standard ICC tagged `ASSUMPTION-DEPENDENT` |
| Missing data | Per §17; ICC computed on complete cases with reported coverage |
| CI | Bootstrap |

If ordinal nature makes standard ICC inappropriate for primary analysis, ICC is **demoted to secondary/sensitivity**; weighted κ and Krippendorff α become primary.

### 11.3 Bradley-Terry — Full Specification

| Item | Specification |
|------|---------------|
| Comparison graph | Reported density, connectivity check |
| Ties | Modeled (BT with ties / Davidson model); tie policy documented |
| Intransitivity | **Tested** (e.g., triangle consistency); reported rate |
| Balance | Comparison counts per pair reported; order balanced |
| Sparse graphs | Regularized BT; disconnected components flagged |
| CI | Bootstrap / profile likelihood |

### 11.4 Agreement Below Target (New)

If `κw < target`: do **not** lower the target. Instead inspect, in order: rubric ambiguity → evaluator training → dimension overlap → label distribution → prevalence effects. May require **rubric revision + repeat pilot**.

---

## 12. PS-03 Calibration Methodology (Revised — H04, H07)

### 12.1 Dimension-Level Calibration

| Step | Method |
|------|--------|
| Metric Extraction | Run PS-03 on all candidates |
| Human Alignment | Match PS-03 dim to human ordinal dim |
| Association | **Spearman ρ (primary)**; Kendall τ secondary; Pearson exploratory-only |
| Calibration Curve | **Penalized isotonic regression** (cross-validated penalty) |
| Discrimination | ROC/PR on binary ACCEPT/REJECT |

### 12.2 Aggregate Calibration

| Step | Method |
|------|--------|
| Weight Optimization | Constrained, regularized optimization |
| Bounds | [0,1] sums to 1 (or [0,100] sums to 100) |
| Regularization | L2; penalty λ chosen by **nested CV** |
| Validation | **Nested CV**: inner tune λ/weights, outer estimate performance |
| Holdout | Final frozen weights evaluated once on holdout |

### 12.3 Calibration Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Spearman ρ (dimension) | ≥0.50 | PRE-REGISTERED TARGET |
| Spearman ρ (aggregate) | ≥0.65 | PRE-REGISTERED TARGET |
| AUC (binary) | ≥0.80 | PRE-REGISTERED TARGET |
| ECE | ≤0.05 | PRE-REGISTERED TARGET |

**All targets PRE-REGISTERED; none VALIDATED.**

### 12.4 Correlation ≠ Agreement (New — S7-10 principle)

Promotion requires **association AND classification performance** (agreement / calibration / FP-FN), never correlation alone.

---

## 13. Weight Optimization Safeguards (Revised — H07)

### 13.1 n_eff / Parameters Ratio

| Rule | Requirement |
|------|-------------|
| Parameters | 6 (dimension weights) |
| Minimum ratio | **n_eff / params ≥ 10** |
| If violated | Reduce dimensions (via §8) OR do not optimize |

### 13.2 Nested Cross-Validation

```
Outer CV (grouped by chapter)
   └── Inner CV → λ / weight selection
Outer fold → performance estimate
Final → holdout (once)
```

Prohibited: `5-fold CV → choose weights → report same CV as validation`.

### 13.3 Weight Stability Analysis

Report per-fold weights. Flag `UNSTABLE` if any dimension's weight: range > 0.15, sign change, or CV > 0.30. Report all folds, not only the mean.

### 13.4 Weight Constraints (TBD)

`non-negative? sum-to-one? max/min per dimension?` — **TBD — pre-calibration methodology choice**, to be fixed before calibration with documented rationale. No silent hard-coding.

### 13.5 Promotion Rule

`optimal weight ≠ validated production weight`. Promotion requires nested validation + stability + holdout + human alignment.

---

## 14. Threshold Calibration (Revised — H06, S7-10 §5.15)

### 14.1 Frozen Thresholds

`80 / 65` remain **FROZEN and UNCALIBRATED**. v1.1 only defines how a future task might *evaluate* them — never replace, re-tune, or promote.

### 14.2 Cost Ratio (Revised)

`FP:FN = 3:1` is reclassified **UNSUPPORTED ASSUMPTION**. v1.1 defines it as a **Candidate operational cost ratio**, requiring before calibration:
- Operational impact analysis
- Stakeholder-approved cost model
- Sensitivity analysis across 1:1, 2:1, 3:1, and higher

### 14.3 Primary vs Secondary Criteria

| Criterion | Role |
|-----------|------|
| Cost-sensitive (minimize expected cost at approved ratio) | **Primary** |
| Youden Index | Secondary/sensitivity |
| PR curve | Reported (esp. under class imbalance) |
| ROC curve | Reported |
| Confusion matrix | Reported at chosen threshold |

**Pre-registered**; no “run-many-then-pick-best”.

### 14.4 Class Balance

If ACCEPT/REJECT prevalence is imbalanced, PR analysis is **more informative** than ROC; report both balanced and realistic-prevalence results.

---

## 15. Validation / Holdout (Revised — S7-10 §5.4)

| Set | Proportion | Unit | Purpose |
|-----|------------|------|---------|
| Calibration | 60% | chapter group | Weight/threshold fitting |
| Validation | 20% | chapter group | Hyperparameter selection |
| Holdout | 20% | chapter group | Final unbiased evaluation |

**Grouped by chapter and author.** Nested CV inside calibration. No chapter/scene/author crosses splits.

### Statistical Validity (Revised)

| Requirement | v1.0 | v1.1 |
|-------------|------|------|
| Holdout passages | ≥100 raw | **n_eff ≥ 100** |
| Holdout chapters | ≥10 | ≥10 |
| Evaluator coverage | ≥3 | ≥3 (PRE-REGISTERED PILOT TARGET) |

---

## 16. Leakage / Bias Controls (Revised — H08, S7-10 §5.5)

### 16.1 Role Separation (New — H08)

| Role | Definition | Constraint |
|------|------------|------------|
| Reference Creator | Produces GOLD/SILVER | ≠ Primary Evaluator |
| Reference Reviewer | Reviews reference | ≠ Primary Evaluator (when conflict) |
| Candidate Generator | Runs translation | May be separate from all |
| Evaluator | Scores candidates | Disjoint from creators |

**Hard rule**: `reference creator ≠ primary evaluator` for the same source passage.

### 16.2 Reference Contamination Prevention

Prohibited:
- Human-edited candidate → same candidate scored by its editor
- Reference creator scores candidates for their own reference source

Enforced via `creator_id` vs `evaluator_id` disjointness check.

### 16.3 Deduplication

| Type | Rule |
|------|------|
| Exact duplicate | Remove |
| Normalized duplicate | Remove |
| Near duplicate | Remove (simhash ≥0.85) |
| Same source / altered punctuation | Remove |
| Same candidate text | Remove across splits |
| Same reference reused | Track; forbid across splits |

### 16.4 Blinding

Evaluators never see: model, provider, attempt number, gold/silver/bronze status, production designation, prompt condition, PS-03 scores.

### 16.5 Order / Carry-over

- A/B order balanced (each pair both orders)
- Randomization per evaluator
- Counterbalancing to limit repeated related pairs
- Position-bias logged

### 16.6 Metric Leakage (New)

Prohibited: PS-03 selects “good” candidates → same human study evaluates only PS-03-selected candidates → PS-03 appears correlated. Candidates must be sampled independently of PS-03.

---

## 17. Missing Data & Outliers (New)

### 17.1 Missing Data Classes

`missing` / `abstain` / `invalid` / `inattentive` / `excluded` — each with a **predefined** rule. No silent deletion, mean imputation, or zero fill.

### 17.2 Outlier Policy

Pre-register outlier handling; **blind to outcome**. Primary analysis + sensitivity analysis both reported. Never remove inconvenient scores post hoc.

---

## 18. Reference Hierarchy (Revised — S7-10 §5.20)

| Class | Creator | Review | Calibration | Validation | Holdout |
|-------|---------|--------|-------------|------------|---------|
| GOLD | Professional translator | ≥2 reviews + adjudication | ✅ | ✅ | ✅ |
| SILVER | Human-edited MT | 1 review + approval | ⚠️ limited | ⚠️ limited | ❌ |
| BRONZE | Single human | None | Diagnostic only | ❌ | ❌ |

**BRONZE cannot be a gold calibration target** without re-validation of quality.

---

## 19. Pairwise Protocols (Revised — S7-10 §5.10, §36)

| Use Case | Changed | Must Remain Identical | Primary Outcome |
|----------|---------|----------------------|-----------------|
| **Best Attempt** | attempt index | source, context | Ordered preference (1 vs 2, 2 vs 3) |
| **Context Continuity** | context availability | model, provider, prompt, source, temperature | Directional preference (ON > OFF) |
| **Reviewer/Editor/ACE** | processing applied | model, provider, source | Directional preference (processed > baseline) |
| **Segment Merge** | merge strategy | source, segment logic | Whole-output quality (merged vs full) |

### 19.1 Symmetric vs Asymmetric

- Symmetric (Best Attempt): two-sided, preference win-rate.
- Asymmetric (Context, Reviewer/Editor/ACE, Segment): **directional**, one-sided tests, report direction.

### 19.2 Targeted Win-Rate Targets

`Context ≥65%`, `Reviewer/Editor/ACE ≥60%`, `Best Attempt ρ ≥0.70` = **PRE-REGISTERED TARGETS**.

### 19.3 Additional Controls

- Context: evaluator **detectability check** (can they guess condition?)
- Best Attempt: control for HARD_GATE status
- Segment: merge strategy **randomized** as experimental factor; human boundary rating added
- Reviewer/Editor/ACE: baseline FP rate from **independent holdout** (not same data)

---

## 20. Fatigue / Training (Revised — S7-10 §37, §38)

| Item | v1.1 |
|------|------|
| Max items/session | **TBD — pilot determines operational value** |
| Break policy | Mandatory breaks; TBD from pilot |
| Session duration | TBD from pilot |
| Randomization | Per evaluator |
| Practice items | Yes, disjoint from all splits |
| Attention checks | Yes, embedded |
| Repeat items | 10% intra-rater; excluded from formal analysis |

Training set / practice set / evaluation set / holdout set are **mutually exclusive**; training examples never leak into holdout.

---

## 21. Pre-Registration (New — S7-10 §44)

Required before calibration execution:

```
primary endpoint
secondary endpoints
primary metric
primary agreement method
sampling rule
split rule
exclusion criteria
missing-data rules
candidate threshold procedure
cost assumptions
stopping criteria
promotion rule
```

### 21.1 Confirmatory vs Exploratory

| Type | Content | Promotion Weight |
|------|---------|------------------|
| Confirmatory | Primary outcome/method/hypothesis/threshold | May support promotion |
| Exploratory | Alternate weights/metrics/thresholds/subgroups | **Cannot automatically promote** |

---

## 22. Multiple Comparisons / Target Shopping (New — S7-10 §29, §54)

- Pre-register primary analysis.
- Label exploratory analyses.
- **No post-hoc target selection** (`κ=0.54 → choose 0.50`).
- **No metric cherry-picking** after seeing results.

---

## 23. Stopping Criteria (Revised — S7-10 §53)

| Condition | Action |
|-----------|--------|
| Stable validation (±0.02 over 3 epochs) | Proceed to holdout |
| Diverging validation | Revise methodology |
| Cost > cap | Scope reduction |
| Agreement < 0.40 after revision | Abandon metric |
| Result-dependent stopping | **PROHIBITED** |

No optional stopping. No “good → stop, bad → collect more”.

---

## 24. Cost / Value (Revised — S7-10 §25)

`net value > cost` operationalized as a framework (not monetary):

```
evaluation cost
reviewer burden
engineering burden
false-positive cost
false-negative cost
maintenance burden
quality benefit
```

No invented monetary values. Preserves `NOT_WORTH_PROMOTING_TO_PRODUCTION_GATE` if evidence shows weak alignment / unstable threshold / high FP risk / high burden / low value.

---

## 25. Dataset Schema (Revised)

v1.0 schema retained; added fields:

| Table | New Field | Purpose |
|-------|-----------|---------|
| `sources` | `author_id` | Author-level clustering |
| `sources` | `terminology_group_id` | Term-batch clustering |
| `references` | `creator_id` | Role separation (H08) |
| `references` | `reviewer_ids[]` | Role separation |
| `evaluations` | `label_conflict` | Binary/Likert conflict flag |
| `evaluations` | `attention_check_passed` | Data validity |
| `candidates` | `selection_independent_of_ps03` | Metric-leakage guard |

---

## 26. Numerical Target Registry (New — H06)

| Metric / Rule | Value | v1.1 Status | Why | Upgrade Evidence |
|---------------|------:|-------------|-----|------------------|
| Pilot passages | 50 | **PILOT_ONLY** | Feasibility only | n/a |
| Evaluators | 3–5 | **PRE-REGISTERED PILOT TARGET** | No reliability basis | Reliability/power analysis |
| κw | ≥0.60 | **PRE-REGISTERED TARGET** | No empirical basis | Empirical agreement study |
| Best Attempt ρ | ≥0.70 | **PRE-REGISTERED TARGET** | No empirical basis | Human-preference validation |
| Context win rate | ≥65% | **PRE-REGISTERED TARGET** | No empirical basis | Controlled A/B |
| Reviewer/Editor/ACE | ≥60% | **PRE-REGISTERED TARGET** | No empirical basis | Controlled comparison |
| FP:FN cost | 3:1 | **UNSUPPORTED ASSUMPTION** | No operational data | Cost study |
| Split | 60/20/20 | **PRE-REGISTERED TARGET** | Standard, unverified for clustered data | Dependency/power analysis |
| Spearman ρ dim | ≥0.50 | **PRE-REGISTERED TARGET** | No empirical basis | Calibration study |
| Spearman ρ agg | ≥0.65 | **PRE-REGISTERED TARGET** | No empirical basis | Calibration study |
| AUC | ≥0.80 | **PRE-REGISTERED TARGET** | No empirical basis | Calibration study |
| ECE | ≤0.05 | **PRE-REGISTERED TARGET** | No empirical basis | Calibration study |

**No value is VALIDATED.** No value may be described as a production threshold.

---

## 27. Statistical Method Matrix (New)

| Question | Data Type | Primary | Secondary / Sensitivity | Assumptions |
|----------|-----------|---------|-------------------------|-------------|
| Human ordinal rating | ordinal | Report distribution | — | ordinal |
| Inter-rater agreement | ordinal categorical | Weighted κ (quadratic) | ICC-ordinal, Krippendorff α | ordinal |
| Pairwise preference | binary/pairwise | Bradley-Terry | Win-rate + bootstrap | transitivity tested |
| Metric-human association | ordinal/continuous | Spearman ρ | Kendall τ; Pearson exploratory | monotonic |
| Threshold discrimination | binary | Cost-sensitive (approved ratio) | Youden, ROC, PR | cost model |
| Weight optimization | multivariate | Nested-CV regularized | Stability analysis | n_eff/params ≥10 |
| Factor structure | ordinal dimensions | Ordinal EFA (polychoric) | PCA diagnostic | ordinal |

---

## 28. Sample Size Matrix (New)

| Analysis | Primary Parameter | Required Assumption | Raw N | Cluster Adjust | Effective N | Status |
|----------|-------------------|---------------------|------:|----------------|------------:|--------|
| Naturalness correlation | ρ | effect size, α, β | TBD | ×DE | TBD | TBD |
| Agreement | κw, CI width | κ, raters | TBD | ×DE | TBD | TBD |
| Weight optimization | n_eff/params ≥10 | params=6 | TBD | ×DE | TBD | TBD |
| Pairwise preference | win-rate CI | expected rate | TBD | ×DE | TBD | TBD |
| Pilot | feasibility | — | 50 | cluster-aware | — | **PILOT_ONLY** |

Raw N is **never** the final requirement.

---

## 29. Bias / Leakage Matrix (New)

| Risk | Example | Detection | Prevention | Severity |
|------|---------|-----------|------------|----------|
| Chapter leakage | chapter across splits | source grouping | chapter-level split | HIGH |
| Near duplicate | passage variants | simhash | exclusion | HIGH |
| Reference contamination | creator = evaluator | provenance metadata | role separation | CRITICAL |
| Position bias | A always first | order logs | randomization | MEDIUM |
| Learning effect | repeated similar pairs | evaluator history | balancing | MEDIUM |
| Metric leakage | PS-03 selects sample | candidate provenance | independent sampling | CRITICAL |
| Overfitting | tune on validation | CV audit | nested CV | HIGH |
| Target shopping | post-hoc threshold | pre-registration check | pre-register | HIGH |

---

## 30. Pilot Study (Revised — H01)

### 30.1 Pilot Purpose (Explicit)

Pilot answers **only**: rubric usable? agreement plausible? protocol feasible? sampling workable? fatigue manageable? It does **not** prove production quality.

### 30.2 Pilot Scope

| Item | Target |
|------|--------|
| Passages | 50 (stratified, feasibility) |
| Evaluators | 3–5 |
| Candidates/passage | 2–3 |
| Duration | 2–3 weeks |

### 30.3 Pilot Outputs → Go / Revise / No-Go

Pilot determines rubric/protocol revisions and gates a future **separate** calibration task.

---

## 31. Calibration Readiness Pipeline (Revised)

```
Design v1.1
   ↓
Re-Audit (S7-12)
   ↓
Pilot execution (separate task)
   ↓
Pilot review
   ↓
Calibration execution (separate task)
   ↓
Calibration analysis
   ↓
Independent validation
   ↓
Holdout
   ↓
Contract promotion review
```

**Prohibited**: `Design complete → Production gate`.

---

## 32. Production Boundary (Frozen)

| Boundary | Status |
|----------|--------|
| PS-03 production behavior | UNCHANGED |
| QualityResult / gate / retry | UNCHANGED |
| Provider selection / translation runtime | UNCHANGED |
| Model `meta/llama-3.2-90b-vision-instruct` | FROZEN |
| Provider `nvidia` | FROZEN |
| Retry boundary | FROZEN |
| `quality_context_scene_v72=false` | FROZEN OFF |
| PS-03 weights 30/20/20/15/10/5 | FROZEN |
| Thresholds 80/65 | FROZEN |

---

## 33. Explicit Non-Goals

Calibration execution, human study, dataset collection, reference creation, PS-03 changes, threshold changes, retry changes, context activation, Best Attempt / Segment / Reviewer / Editor / ACE implementation, model/provider change.

---

## 34. Revision Acceptance Conditions

| Condition | Status |
|-----------|--------|
| H01: 50 explicitly PILOT_ONLY | ✅ |
| H02: cluster-aware n_eff framework | ✅ |
| H03: rubric overlap addressed | ✅ |
| H04: ordinal methodology corrected | ✅ |
| H05: agreement metrics fully specified | ✅ |
| H06: all numerical targets classified | ✅ |
| H07: weight optimization safeguards | ✅ |
| H08: reference contamination prevented | ✅ |

---

*End of Design v1.1*

**Design Path**: `artifacts/NTPE_S7_11_LITERARY_QUALITY_EVALUATION_CALIBRATION_DESIGN_V1_1.md`
**Status**: `REVISION_01_COMPLETE`